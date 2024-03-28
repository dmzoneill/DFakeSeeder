import unittest
from unittest.mock import patch
from d_fake_seeder.lib.util.helpers import (
    sizeof_fmt,
    urlencode,
    random_id,
    humanbytes,
    convert_seconds_to_hours_mins_seconds,
    add_kb,
    add_percent,
)
import pytest


class TestHelperFunctions(unittest.TestCase):
    @pytest.mark.timeout(5)
    def test_sizeof_fmt(self):
        result = sizeof_fmt(1024)
        self.assertEqual(result, "1.0KB")

        result = sizeof_fmt(2048)
        self.assertEqual(result, "2.0KB")

        result = sizeof_fmt(1048576)
        self.assertEqual(result, "1.0MB")

    @pytest.mark.timeout(5)
    def test_urlencode(self):
        result = urlencode(b"Hello World")
        self.assertEqual(result, "Hello+World")

        result = urlencode(b"https://www.example.com")
        self.assertEqual(result, "https:%2F%2Fwww.example.com")

    @pytest.mark.timeout(5)
    def test_random_id(self):
        result = random_id(10)
        self.assertEqual(len(result), 10)

        result = random_id(5)
        self.assertEqual(len(result), 5)

    @pytest.mark.timeout(5)
    def test_humanbytes(self):
        result = humanbytes(1024)
        self.assertEqual(result, "1.0 KB")

        result = humanbytes(2048)
        self.assertEqual(result, "2.0 KB")

        result = humanbytes(1048576)
        self.assertEqual(result, "1.0 MB")

    @pytest.mark.timeout(5)
    def test_convert_seconds_to_hours_mins_seconds(self):
        result = convert_seconds_to_hours_mins_seconds(3665)
        self.assertEqual(result, "1h 1m 5s")

        result = convert_seconds_to_hours_mins_seconds(7250)
        self.assertEqual(result, "2h 0m 50s")

    @pytest.mark.timeout(5)
    def test_add_kb(self):
        result = add_kb(1024)
        self.assertEqual(result, "1024 kb")

        result = add_kb(2048)
        self.assertEqual(result, "2048 kb")

    @pytest.mark.timeout(5)
    def test_add_percent(self):
        result = add_percent(50)
        self.assertEqual(result, "50 %")

        result = add_percent(75)
        self.assertEqual(result, "75 %")


if __name__ == "__main__":
    unittest.main()
