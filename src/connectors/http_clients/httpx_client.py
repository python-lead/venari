import asyncio
import random

import time
from logging import Logger
from typing import Optional

import httpx

from connectors.connector_interface import ConnectorInterface
from connectors.http_clients.http_client_interfaces import (
    AsyncHttpClientInterface,
    Response,
)


class HttpxClient(ConnectorInterface, AsyncHttpClientInterface):
    """
    httpx based async client

    Supports:
    - httpx client connection pooling
    - concurrency limits using semaphore
    - retry + exponential backoff + jitter
    - timeouts
    - optional circuit breaker

    # todo:
     - Implement token bucket rate limiting
     - Circuit breaker should be a separate injected object
    """

    def __init__(
        self,
        max_concurrency: int = 50,
        request_timeout: int = 10,
        max_retries: int = 5,
        backoff_factor: float = 0.3,
        logger: Optional[Logger] = None,
        enable_circuit_breaker: bool = True,
        circuit_breaker_fail_threshold: int = 4,
        circuit_breaker_reset_time: int = 10,
        circuit_breaker_max_reopens: int = 3,  # Terminate client threshold
        max_wait_for_open_circuit: int = 15,  # Maximal wait time for circuit to open
    ):
        """
        circuit_breaker_opening_threshold: How many consecutive failures must happen before the circuit breaker opens
        circuit_breaker_max_reopens: How many consecutive circuit breaker reopens before requests get terminated
        """
        self.client: Optional[httpx.AsyncClient] = None
        self.semaphore = asyncio.Semaphore(max_concurrency)

        self.timeout = request_timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logger

        # connection limits
        self.limits = httpx.Limits(
            max_keepalive_connections=max_concurrency,
            max_connections=max_concurrency,
        )

        # circuit breaker
        self.enable_circuit_breaker = enable_circuit_breaker
        self.circuit_breaker_opening_threshold = circuit_breaker_fail_threshold
        self.circuit_breaker_reset_time = circuit_breaker_reset_time
        self.circuit_breaker_max_reopens = circuit_breaker_max_reopens
        self.circuit_breaker_max_wait_for_open = max_wait_for_open_circuit
        self.circuit_breaker_successive_request_fail_count = 0
        self.circuit_open_until: Optional[float] = None
        self.circuit_reopen_count = 0
        self.circuit_breaker_half_open = False

    async def start(self) -> None:
        """
        Setup client explicitly
        """
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=self.limits,
        )

    async def get(self, url, tracking_id: Optional[str] = None) -> Response:
        if not self.client:
            raise RuntimeError(
                "HttpxClient client must be initiated with .start() before use"
            )

        if self._circuit_is_open():
            # In case of circuit break being OPEN
            wait_time = self.circuit_open_until - time.time()

            if wait_time > self.circuit_breaker_max_wait_for_open:
                # Open state wait time can't be longer than circuit_breaker_max_wait_for_open
                wait_time = self.circuit_breaker_max_wait_for_open

            if self.logger:
                self.logger.warning(
                    f"[HttpxClient]{tracking_id} - Circuit OPEN — delaying request {wait_time:.2f}s"
                )
            await asyncio.sleep(wait_time)

            # after sleeping, allow only 1 task through (half-open)
            self.circuit_breaker_half_open = True

        # Limits concurrent task executions
        async with self.semaphore:
            last_exception = None

            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.circuit_breaker_half_open:
                        # jittered delay BEFORE request in half-open mode
                        wait_time = random.uniform(0.01, 0.3)
                        await asyncio.sleep(wait_time)

                    response = await self.client.get(url)
                    response.raise_for_status()
                    self._on_request_success()
                    return response

                except (
                    httpx.ReadTimeout,
                    httpx.ConnectTimeout,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                ) as exc:
                    last_exception = exc
                    self._on_request_failure(tracking_id=tracking_id)

                    if attempt == self.max_retries:
                        raise

                    # exponential backoff
                    wait_time = (
                        self.backoff_factor * (2 ** (attempt - 1))
                        + random.random()
                        * 0.1  # random jitter, decrease a chance a bunch of retries happening at once
                    )

                    if self.logger:
                        self.logger.debug(
                            f"[HttpxClient]{tracking_id} - Retry {attempt}/{self.max_retries} for {url}, "
                            f"sleep={wait_time:.2f}s, err={exc}"
                        )
                    await asyncio.sleep(wait_time)

                except httpx.HTTPError as exc:
                    if self.logger:
                        self.logger.error(
                            f"[HttpxClient]{tracking_id} - Non-retryable HTTP error for URL={url}: {exc}"
                        )
                    raise

                except Exception as exc:
                    if self.logger:
                        self.logger.error(
                            f"[HttpxClient]{tracking_id} - Unknown exception: {exc}"
                        )
                    raise

            raise last_exception

    def _on_request_success(self):
        if self.enable_circuit_breaker:
            # Reset circuit_breaker
            self.circuit_breaker_successive_request_fail_count = 0
            self.circuit_open_until = None

            if self.circuit_breaker_half_open:
                self.circuit_breaker_half_open = False
                self.circuit_reopen_count = 0

    def _on_request_failure(self, tracking_id: Optional[str] = None):
        if self.enable_circuit_breaker:
            self.circuit_breaker_successive_request_fail_count += 1
            if (
                self.circuit_breaker_successive_request_fail_count
                >= self.circuit_breaker_opening_threshold
            ):
                # OPEN the breaker circuit
                self.circuit_open_until = time.time() + self.circuit_breaker_reset_time
                self.circuit_reopen_count += 1
                self.circuit_breaker_successive_request_fail_count = (
                    0  # reset request failure count
                )

                if self.logger:
                    self.logger.error(
                        f"[HttpxClient]{tracking_id} Circuit breaker OPEN — "
                        f"will reset in {self.circuit_breaker_reset_time}s "
                        f"(reopens: {self.circuit_reopen_count})"
                    )

                if self.circuit_reopen_count >= self.circuit_breaker_max_reopens:
                    if self.logger:
                        self.logger.error(
                            f"[HttpxClient]{tracking_id} Circuit breaker failure threshold reached!"
                        )
                    raise RuntimeError(
                        "[HttpxClient] Circuit breaker failure threshold reached — aborting scrape"
                    )

    def _circuit_is_open(self) -> bool:
        if not self.enable_circuit_breaker:
            return False

        if self.circuit_open_until:
            if time.time() < self.circuit_open_until:
                # breaker still OPEN
                return True
            else:
                # breaker wait time expired, move to HALF-OPEN state
                self.circuit_breaker_half_open = True
                return False
        return False

    async def terminate(self) -> None:
        await self.client.aclose()
        self.client = None
