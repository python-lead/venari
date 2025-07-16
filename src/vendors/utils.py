from typing import Optional


def try_int(val: str) -> Optional[int]:
    try:
        return int(val.replace(" ", "").replace("K", "000"))
    except Exception:
        return None
