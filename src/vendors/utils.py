import logging
from typing import Optional

logger = logging.getLogger(__name__)


def try_int(val: str) -> Optional[int]:
    try:
        return int(val.replace(" ", "").replace("K", "000"))
    except Exception:
        return None


def convert_salary_to_hourly_range(
    min_val: int, max_val: int, unit: str
) -> tuple[Optional[int], Optional[int]]:
    """
    Converts salary to hourly range if unit is supported
    """
    if "/month" in unit.lower():
        return min_val // 160, max_val // 160
    elif "/h" in unit.lower():
        return min_val, max_val
    elif "/day" in unit.lower():
        return min_val // 8, max_val // 8
    elif "/year" in unit.lower():
        # 2080 - work hours in a year
        return min_val // 2080, max_val // 2080

    logger.warning(
        f"convert_salary_to_hourly_range encountered unsupported unit: {unit}"
    )
    return None, None
