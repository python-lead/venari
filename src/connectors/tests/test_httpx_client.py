import unittest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from connectors.http_clients.httpx_client import HttpxClient


class HttpxClientCircuitBreakerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.time_patch = patch("time.time")
        self.mock_time = self.time_patch.start()
        self.mock_time.return_value = 1000.0

    async def asyncTearDown(self):
        self.time_patch.stop()

    @staticmethod
    async def run_fail(client: HttpxClient, tracking_id: str):
        """Force httpx failure for next request"""
        failure_exc = httpx.ConnectError("Simulated failure")
        client.client.get.side_effect = failure_exc
        return await client.get("http://test", tracking_id=tracking_id)

    @staticmethod
    async def run_success(client: HttpxClient, tracking_id: str):
        """Force httpx success for next request"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.text = "<ok />"

        client.client.get.side_effect = lambda url: mock_response
        return await client.get("http://test", tracking_id=tracking_id)

    async def test_no_cb_when_success_only(self):
        """Circuit breaker not activating if circuit_breaker_fail_threshold is not reached"""
        client = HttpxClient(
            max_concurrency=2,
            max_retries=1,
            backoff_factor=0.1,
            circuit_breaker_opening_threshold=1,
            circuit_breaker_reset_time=5,
            circuit_breaker_max_reopens=1,
            enable_circuit_breaker=True,
        )

        client.client = AsyncMock()

        for tracking_id in ["S1", "S2", "S3"]:
            resp = await self.run_success(client, tracking_id)
            self.assertEqual(resp.text, "<ok />")

        self.assertEqual(client.circuit_breaker_successive_request_fail_count, 0)
        self.assertEqual(client.circuit_reopen_count, 0)
        self.assertFalse(client.circuit_breaker_half_open)
        self.assertIsNone(client.circuit_open_until)

    async def test_cb_opens_on_failures(self):
        """
        Circuit breaker opens upon reaching circuit_breaker_fail_threshold
        """
        client = HttpxClient(
            max_concurrency=2,
            max_retries=1,
            backoff_factor=0.1,
            circuit_breaker_opening_threshold=2,
            circuit_breaker_reset_time=5,
            circuit_breaker_max_reopens=5,
            enable_circuit_breaker=True,
        )

        client.client = AsyncMock()

        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, "A1")

        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, "A2")

        # CB should have opened once
        self.assertEqual(client.circuit_reopen_count, 1)
        self.assertIsNotNone(client.circuit_open_until)

    async def test_cb_resets_after_half_open_success(self):
        """
        Circuit breaker closes after successful request
        """
        client = HttpxClient(
            max_concurrency=1,
            max_retries=1,
            backoff_factor=0.1,
            circuit_breaker_opening_threshold=2,
            circuit_breaker_reset_time=5,
            circuit_breaker_max_reopens=5,
            enable_circuit_breaker=True,
        )

        client.client = AsyncMock()

        # Opening circuit breaker
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, "F1")

        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, "F2")

        self.assertEqual(client.circuit_reopen_count, 1)
        self.assertIsNotNone(client.circuit_open_until)

        # Move time beyond open window → HALF-OPEN
        self.mock_time.return_value += client.circuit_breaker_reset_time + 0.1

        # measure sleep to confirm half-open jitter executed
        last_slept_durations: float | None = None

        async def fake_sleep(dur):
            nonlocal last_slept_durations
            last_slept_durations = dur
            self.mock_time.return_value += dur

        with patch("asyncio.sleep", side_effect=fake_sleep):
            resp = await self.run_success(client, "HALFOPEN-S1")

        # validate jitter occurred
        self.assertIsNotNone(last_slept_durations)
        self.assertTrue(
            0.009 <= last_slept_durations <= 0.31,
            f"Expected 0.01–0.3 jitter in HALF-OPEN; got {last_slept_durations}",
        )

        # verify breaker is fully reset after successful half-open call
        self.assertEqual(client.circuit_breaker_successive_request_fail_count, 0)
        self.assertFalse(client.circuit_breaker_half_open)
        self.assertIsNone(client.circuit_open_until)
        self.assertEqual(resp.text, "<ok />")

    async def test_circuit_breaker_max_reopen_termination(self):
        """
        Circuit breaker should terminate requests after reaching max reopen threshold
        - repeated failures → multiple CB openings
        - max reopen threshold → RuntimeError
        """
        client = HttpxClient(
            max_concurrency=1,
            max_retries=1,
            backoff_factor=0.1,
            circuit_breaker_opening_threshold=2,  # OPEN after 2 failures
            circuit_breaker_reset_time=5,  # stays open 5s
            circuit_breaker_max_reopens=3,  # kill after 3 openings
            enable_circuit_breaker=True,
        )

        client.client = AsyncMock()

        tracking_ids = ["A1", "B2", "C3", "D4", "E5", "F6", "SUCCESS-1"]

        # First CB opening
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, tracking_ids[0])
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, tracking_ids[1])

        self.assertEqual(client.circuit_reopen_count, 1)
        self.assertIsNotNone(client.circuit_open_until)

        # Advance time beyond open period
        self.mock_time.return_value += client.circuit_breaker_reset_time + 0.1

        # Second CB opening
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, tracking_ids[2])
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, tracking_ids[3])

        self.assertEqual(client.circuit_reopen_count, 2)

        # Advance time
        self.mock_time.return_value += client.circuit_breaker_reset_time + 0.1

        # Third CB opening, hitting failure threshold
        with self.assertRaises(httpx.ConnectError):
            await self.run_fail(client, tracking_ids[4])

        # Hitting threshold on next failure → RuntimeError
        with self.assertRaises(RuntimeError):
            await self.run_fail(client, tracking_ids[5])

        self.assertEqual(client.circuit_reopen_count, 3)


if __name__ == "__main__":
    unittest.main()
