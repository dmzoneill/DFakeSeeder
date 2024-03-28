import unittest
import logging
import os
from d_fake_seeder.lib.logger import ClassNameFilter
import pytest


class TestClassNameFilter(unittest.TestCase):
    def setUp(self):
        self.filter = ClassNameFilter()

    @pytest.mark.timeout(5)
    def test_filter_record_no_class_name(self):
        record = logging.LogRecord(
            "name", logging.INFO, "pathname", 1, "message", (), None
        )
        filtered = self.filter.filter(record)
        self.assertTrue(hasattr(record, "class_name"))
        self.assertEqual(record.class_name, "name")
        self.assertTrue(filtered)

    @pytest.mark.timeout(5)
    def test_filter_record_with_class_name(self):
        record = logging.LogRecord(
            "name", logging.INFO, "pathname", 1, "message", (), None
        )
        record.class_name = "custom_class"
        filtered = self.filter.filter(record)
        self.assertEqual(record.class_name, "custom_class")
        self.assertTrue(filtered)


if __name__ == "__main__":
    unittest.main()
