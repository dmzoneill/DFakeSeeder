"""
Utility Helper Functions.

This module provides common utility functions used throughout the DFakeSeeder
application, including human-readable byte formatting, URL encoding for
BitTorrent protocols, and random string generation.
"""

# fmt: off
import random
import string
from typing import Any

# fmt: on


def sizeof_fmt(num: Any, suffix: Any = "B") -> Any:
    """Format size of file in a readable format."""
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def urlencode(data: Any) -> Any:
    """Encode a byte array in URL format."""
    result = ""
    valids = (string.ascii_letters + "_.").encode("ascii")
    for b in data:
        if b in valids:
            result += chr(b)
        elif b == " ":
            result += "+"
        else:
            result += f"%{b:02X}"
    return result


def random_id(length: Any) -> Any:
    """Generate a random ID of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def humanbytes(B: Any) -> Any:  # pylint: disable=invalid-name
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)  # pylint: disable=invalid-name
    KB = float(1024)  # pylint: disable=invalid-name
    MB = float(KB**2)  # 1,048,576  # pylint: disable=invalid-name
    GB = float(KB**3)  # 1,073,741,824  # pylint: disable=invalid-name
    TB = float(KB**4)  # 1,099,511,627,776  # pylint: disable=invalid-name

    if B < KB:
        val = int(B) if B.is_integer() else B
        return f"{val} B"
    if KB <= B < MB:
        val = int(B / KB) if (B / KB).is_integer() else f"{B / KB:.2f}".rstrip("0").rstrip(".")
        return f"{val} KB"
    if MB <= B < GB:
        val = int(B / MB) if (B / MB).is_integer() else f"{B / MB:.2f}".rstrip("0").rstrip(".")
        return f"{val} MB"
    if GB <= B < TB:
        val = int(B / GB) if (B / GB).is_integer() else f"{B / GB:.2f}".rstrip("0").rstrip(".")
        return f"{val} GB"
    if TB <= B:
        val = int(B / TB) if (B / TB).is_integer() else f"{B / TB:.2f}".rstrip("0").rstrip(".")
        return f"{val} TB"
    return "0 B"  # Fallback for edge cases


def convert_seconds_to_hours_mins_seconds(seconds: Any) -> Any:
    """Convert seconds to human-readable time string (Xh Xm Xs)."""
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    mins = remaining_seconds // 60
    remaining_seconds = remaining_seconds % 60

    time_str = ""
    if hours > 0:
        time_str += f"{hours}h "
    if mins > 0:
        time_str += f"{mins}m "
    if remaining_seconds != 0:
        time_str += f"{remaining_seconds}s"

    return time_str


def add_kb(kb: Any) -> None:
    """Format value with kb suffix."""
    return f"{kb} kb"  # type: ignore[return-value]


def add_percent(percent: Any) -> None:
    """Format value with percent suffix."""
    return f"{percent} %"  # type: ignore[return-value]


def format_timestamp(timestamp: Any) -> Any:
    """Convert Unix timestamp to readable date string. Uses current time if blank/invalid."""
    from datetime import datetime

    try:
        ts = int(timestamp) if timestamp else 0
        if ts == 0:
            ts = int(datetime.now().timestamp())
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError, TypeError):
        return datetime.now().strftime("%Y-%m-%d %H:%M")
