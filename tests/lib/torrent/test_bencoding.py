import unittest

import pytest

from d_fake_seeder.lib.torrent.bencoding import decode, encode


class TestBencodingMethods(unittest.TestCase):
    @pytest.mark.timeout(5)
    def test_decode_empty_input(self):
        self.assertIsNone(decode(b""))

    @pytest.mark.timeout(5)
    def test_decode_integer(self):
        self.assertEqual(decode(b"i123e"), 123)

    @pytest.mark.timeout(5)
    def test_decode_string(self):
        self.assertEqual(decode(b"4:test"), b"test")

    @pytest.mark.timeout(5)
    def test_decode_list(self):
        self.assertEqual(decode(b"l3:one3:twoe"), [b"one", b"two"])

    @pytest.mark.timeout(5)
    def test_decode_dict(self):
        self.assertEqual(decode(b"d3:key5:valuee"), {b"key": b"value"})

    @pytest.mark.timeout(5)
    def test_encode_integer(self):
        self.assertEqual(encode(123), b"i123e")

    @pytest.mark.timeout(5)
    def test_encode_string(self):
        self.assertEqual(encode(b"test"), b"4:test")

    @pytest.mark.timeout(5)
    def test_encode_list(self):
        self.assertEqual(encode([b"one", b"two"]), b"l3:one3:twoe")

    @pytest.mark.timeout(5)
    def test_encode_dict(self):
        self.assertEqual(encode({b"key": b"value"}), b"d3:key5:valuee")


if __name__ == "__main__":
    unittest.main()
