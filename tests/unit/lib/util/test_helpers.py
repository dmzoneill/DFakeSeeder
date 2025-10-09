"""
Unit tests for d_fake_seeder.lib.util.helpers module.

Tests pure utility functions for formatting and conversion.
"""

import pytest
from d_fake_seeder.lib.util.helpers import (
    sizeof_fmt,
    humanbytes,
    convert_seconds_to_hours_mins_seconds,
    add_kb,
    add_percent,
    random_id,
    urlencode,
)


def test_sizeof_fmt_formats_bytes_correctly():
    """Test that sizeof_fmt formats byte values in human-readable format"""
    # Arrange & Act & Assert
    assert sizeof_fmt(0) == "0.0B"
    assert sizeof_fmt(512) == "512.0B"
    assert sizeof_fmt(1024) == "1.0KB"


def test_sizeof_fmt_formats_kilobytes_correctly():
    """Test that sizeof_fmt formats kilobyte values correctly"""
    # Arrange & Act & Assert
    assert sizeof_fmt(1536) == "1.5KB"
    assert sizeof_fmt(2048) == "2.0KB"


def test_sizeof_fmt_formats_megabytes_correctly():
    """Test that sizeof_fmt formats megabyte values correctly"""
    # Arrange & Act & Assert
    assert sizeof_fmt(1048576) == "1.0MB"
    assert sizeof_fmt(5242880) == "5.0MB"


def test_sizeof_fmt_formats_gigabytes_correctly():
    """Test that sizeof_fmt formats gigabyte values correctly"""
    # Arrange & Act & Assert
    assert sizeof_fmt(1073741824) == "1.0GB"
    assert sizeof_fmt(2147483648) == "2.0GB"


def test_humanbytes_formats_bytes_correctly():
    """Test that humanbytes formats byte values correctly"""
    # Arrange & Act & Assert
    assert humanbytes(0) == "0 B"
    assert humanbytes(512) == "512 B"


def test_humanbytes_formats_kilobytes_correctly():
    """Test that humanbytes formats kilobyte values correctly"""
    # Arrange & Act & Assert
    assert humanbytes(1024) == "1 KB"
    assert humanbytes(1536) == "1.5 KB"


def test_humanbytes_formats_megabytes_correctly():
    """Test that humanbytes formats megabyte values correctly"""
    # Arrange & Act & Assert
    assert humanbytes(1048576) == "1 MB"
    assert humanbytes(5242880) == "5 MB"


def test_humanbytes_formats_gigabytes_correctly():
    """Test that humanbytes formats gigabyte values correctly"""
    # Arrange & Act & Assert
    assert humanbytes(1073741824) == "1 GB"
    assert humanbytes(2147483648) == "2 GB"


def test_convert_seconds_to_hours_mins_seconds_handles_seconds_only():
    """Test time conversion with seconds only"""
    # Arrange & Act & Assert
    assert convert_seconds_to_hours_mins_seconds(30) == "30s"
    assert convert_seconds_to_hours_mins_seconds(59) == "59s"


def test_convert_seconds_to_hours_mins_seconds_handles_minutes():
    """Test time conversion with minutes and seconds"""
    # Arrange & Act & Assert
    assert convert_seconds_to_hours_mins_seconds(60) == "1m "
    assert convert_seconds_to_hours_mins_seconds(90) == "1m 30s"


def test_convert_seconds_to_hours_mins_seconds_handles_hours():
    """Test time conversion with hours, minutes, and seconds"""
    # Arrange & Act & Assert
    assert convert_seconds_to_hours_mins_seconds(3600) == "1h "
    assert convert_seconds_to_hours_mins_seconds(3661) == "1h 1m 1s"


def test_add_kb_appends_kb_suffix():
    """Test that add_kb appends 'kb' suffix correctly"""
    # Arrange & Act & Assert
    assert add_kb(100) == "100 kb"
    assert add_kb(500) == "500 kb"


def test_add_percent_appends_percent_suffix():
    """Test that add_percent appends '%' suffix correctly"""
    # Arrange & Act & Assert
    assert add_percent(50) == "50 %"
    assert add_percent(100) == "100 %"


def test_random_id_generates_correct_length():
    """Test that random_id generates ID of specified length"""
    # Arrange & Act
    result_5 = random_id(5)
    result_10 = random_id(10)

    # Assert
    assert len(result_5) == 5
    assert len(result_10) == 10


def test_random_id_contains_alphanumeric_only():
    """Test that random_id contains only alphanumeric characters"""
    # Arrange & Act
    result = random_id(20)

    # Assert
    assert result.isalnum()


def test_urlencode_handles_valid_ascii():
    """Test that urlencode preserves valid ASCII characters"""
    # Arrange
    input_bytes = b"abc_."

    # Act
    result = urlencode(input_bytes)

    # Assert
    assert result == "abc_."


def test_urlencode_handles_spaces():
    """Test that urlencode encodes spaces"""
    # Arrange
    input_bytes = b"hello world"

    # Act
    result = urlencode(input_bytes)

    # Assert
    # Note: The actual implementation uses %20 for spaces in byte strings
    # because b" " is the integer 32 (0x20), not the string " "
    assert "hello%20world" == result


def test_urlencode_handles_special_characters():
    """Test that urlencode percent-encodes special characters"""
    # Arrange
    input_bytes = b"\x00\xff"

    # Act
    result = urlencode(input_bytes)

    # Assert
    assert result == "%00%FF"
