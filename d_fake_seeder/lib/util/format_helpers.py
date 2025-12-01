"""
Simple formatting helpers for DFakeSeeder.

This module provides basic formatting functions without localization support.
"""

# fmt: off
import math
from typing import Optional, Union

from .constants import SIZE_UNITS_EXTENDED

# fmt: on


def format_size(bytes_count: Union[int, float], decimal_places: int = 1) -> str:
    """
    Format file size in human-readable format.

    Args:
        bytes_count: Size in bytes
        decimal_places: Number of decimal places to show

    Returns:
        Formatted size string (e.g., "1.5 GB")
    """
    if bytes_count == 0:
        return "0 B"

    units = SIZE_UNITS_EXTENDED
    unit_index = min(int(math.floor(math.log(abs(bytes_count), 1024))), len(units) - 1)
    size = bytes_count / (1024**unit_index)

    if decimal_places == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.{decimal_places}f} {units[unit_index]}"


def format_number(number: Union[int, float], decimal_places: Optional[int] = None) -> str:
    """
    Format number with appropriate decimal places.

    Args:
        number: Number to format
        decimal_places: Number of decimal places (None for auto)

    Returns:
        Formatted number string
    """
    if decimal_places is None:
        if isinstance(number, int):
            decimal_places = 0
        else:
            decimal_places = 2

    if decimal_places == 0:
        return str(int(number))
    else:
        return f"{number:.{decimal_places}f}"
