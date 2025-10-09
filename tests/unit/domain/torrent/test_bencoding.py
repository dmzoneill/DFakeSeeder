"""
Unit tests for d_fake_seeder.domain.torrent.bencoding module.

Tests Bencoding encode and decode functionality for BitTorrent protocol.
"""

import pytest
from d_fake_seeder.domain.torrent.bencoding import decode, encode


# Decode tests - Bytes strings
def test_decode_simple_string():
    """Test that decode handles simple byte strings"""
    # Arrange
    input_data = b"5:hello"

    # Act
    result = decode(input_data)

    # Assert
    assert result == b"hello"


def test_decode_empty_string():
    """Test that decode handles empty byte strings"""
    # Arrange
    input_data = b"0:"

    # Act
    result = decode(input_data)

    # Assert
    assert result == b""


def test_decode_multidigit_length_string():
    """Test that decode handles strings with multi-digit lengths"""
    # Arrange
    input_data = b"12:hello world!"

    # Act
    result = decode(input_data)

    # Assert
    assert result == b"hello world!"


# Decode tests - Integers
def test_decode_positive_integer():
    """Test that decode handles positive integers"""
    # Arrange
    input_data = b"i42e"

    # Act
    result = decode(input_data)

    # Assert
    assert result == 42


def test_decode_negative_integer():
    """Test that decode handles negative integers"""
    # Arrange
    input_data = b"i-42e"

    # Act
    result = decode(input_data)

    # Assert
    assert result == -42


def test_decode_zero_integer():
    """Test that decode handles zero"""
    # Arrange
    input_data = b"i0e"

    # Act
    result = decode(input_data)

    # Assert
    assert result == 0


# Decode tests - Lists
def test_decode_simple_list():
    """Test that decode handles simple lists"""
    # Arrange
    input_data = b"li1ei2ei3ee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == [1, 2, 3]


def test_decode_empty_list():
    """Test that decode handles empty lists"""
    # Arrange
    input_data = b"le"

    # Act
    result = decode(input_data)

    # Assert
    assert result == []


def test_decode_mixed_list():
    """Test that decode handles lists with mixed types"""
    # Arrange
    input_data = b"li42e5:helloe"

    # Act
    result = decode(input_data)

    # Assert
    assert result == [42, b"hello"]


def test_decode_nested_list():
    """Test that decode handles nested lists"""
    # Arrange
    input_data = b"lli1ei2eeli3ei4eee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == [[1, 2], [3, 4]]


# Decode tests - Dictionaries
def test_decode_simple_dict():
    """Test that decode handles simple dictionaries"""
    # Arrange
    input_data = b"d3:key5:valuee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {b"key": b"value"}


def test_decode_empty_dict():
    """Test that decode handles empty dictionaries"""
    # Arrange
    input_data = b"de"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {}


def test_decode_dict_with_integer_value():
    """Test that decode handles dictionaries with integer values"""
    # Arrange
    input_data = b"d3:agei25ee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {b"age": 25}


def test_decode_dict_with_multiple_keys():
    """Test that decode handles dictionaries with multiple keys"""
    # Arrange
    input_data = b"d4:name4:John3:agei30ee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {b"name": b"John", b"age": 30}


def test_decode_nested_dict():
    """Test that decode handles nested dictionaries"""
    # Arrange
    input_data = b"d4:infod4:name4:Johnee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {b"info": {b"name": b"John"}}


def test_decode_dict_with_list_value():
    """Test that decode handles dictionaries with list values"""
    # Arrange
    input_data = b"d7:numbersli1ei2ei3eee"

    # Act
    result = decode(input_data)

    # Assert
    assert result == {b"numbers": [1, 2, 3]}


# Decode tests - Edge cases
def test_decode_empty_buffer():
    """Test that decode handles empty input buffer"""
    # Arrange
    input_data = b""

    # Act
    result = decode(input_data)

    # Assert
    assert result is None


# Encode tests - Bytes strings
def test_encode_simple_bytes():
    """Test that encode handles simple byte strings"""
    # Arrange
    input_data = b"hello"

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"5:hello"


def test_encode_empty_bytes():
    """Test that encode handles empty byte strings"""
    # Arrange
    input_data = b""

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"0:"


# Encode tests - Strings
def test_encode_simple_string():
    """Test that encode handles simple strings"""
    # Arrange
    input_data = "hello"

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"5:hello"


def test_encode_empty_string():
    """Test that encode handles empty strings"""
    # Arrange
    input_data = ""

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"0:"


# Encode tests - Integers
def test_encode_positive_integer():
    """Test that encode handles positive integers"""
    # Arrange
    input_data = 42

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"i42e"


def test_encode_negative_integer():
    """Test that encode handles negative integers"""
    # Arrange
    input_data = -42

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"i-42e"


def test_encode_zero_integer():
    """Test that encode handles zero"""
    # Arrange
    input_data = 0

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"i0e"


# Encode tests - Lists
def test_encode_simple_list():
    """Test that encode handles simple lists"""
    # Arrange
    input_data = [1, 2, 3]

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"li1ei2ei3ee"


def test_encode_empty_list():
    """Test that encode handles empty lists"""
    # Arrange
    input_data = []

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"le"


def test_encode_mixed_list():
    """Test that encode handles lists with mixed types"""
    # Arrange
    input_data = [42, b"hello"]

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"li42e5:helloe"


def test_encode_nested_list():
    """Test that encode handles nested lists"""
    # Arrange
    input_data = [[1, 2], [3, 4]]

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"lli1ei2eeli3ei4eee"


# Encode tests - Dictionaries
def test_encode_simple_dict():
    """Test that encode handles simple dictionaries"""
    # Arrange
    input_data = {b"key": b"value"}

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"d3:key5:valuee"


def test_encode_empty_dict():
    """Test that encode handles empty dictionaries"""
    # Arrange
    input_data = {}

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"de"


def test_encode_dict_with_integer_value():
    """Test that encode handles dictionaries with integer values"""
    # Arrange
    input_data = {b"age": 25}

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"d3:agei25ee"


def test_encode_dict_with_list_value():
    """Test that encode handles dictionaries with list values"""
    # Arrange
    input_data = {b"numbers": [1, 2, 3]}

    # Act
    result = encode(input_data)

    # Assert
    assert result == b"d7:numbersli1ei2ei3eee"


# Encode tests - Invalid data
def test_encode_invalid_type_raises_error():
    """Test that encode raises ValueError for unsupported types"""
    # Arrange
    input_data = 3.14  # float is not supported

    # Act & Assert
    with pytest.raises(ValueError, match="Unexpected bencode_encode"):
        encode(input_data)


# Round-trip tests
def test_roundtrip_string():
    """Test that encode->decode roundtrip preserves byte strings"""
    # Arrange
    original = b"hello world"

    # Act
    encoded = encode(original)
    decoded = decode(encoded)

    # Assert
    assert decoded == original


def test_roundtrip_integer():
    """Test that encode->decode roundtrip preserves integers"""
    # Arrange
    original = 42

    # Act
    encoded = encode(original)
    decoded = decode(encoded)

    # Assert
    assert decoded == original


def test_roundtrip_list():
    """Test that encode->decode roundtrip preserves lists"""
    # Arrange
    original = [1, b"test", [2, 3]]

    # Act
    encoded = encode(original)
    decoded = decode(encoded)

    # Assert
    assert decoded == original


def test_roundtrip_dict():
    """Test that encode->decode roundtrip preserves dictionaries"""
    # Arrange
    original = {b"name": b"John", b"age": 30, b"hobbies": [b"reading", b"coding"]}

    # Act
    encoded = encode(original)
    decoded = decode(encoded)

    # Assert
    assert decoded == original


def test_roundtrip_complex_structure():
    """Test that encode->decode roundtrip preserves complex nested structures"""
    # Arrange
    original = {
        b"info": {
            b"name": b"example.torrent",
            b"piece length": 16384,
            b"files": [
                {b"path": [b"dir1", b"file1.txt"], b"length": 1024},
                {b"path": [b"dir2", b"file2.txt"], b"length": 2048},
            ],
        },
        b"announce": b"http://tracker.example.com",
    }

    # Act
    encoded = encode(original)
    decoded = decode(encoded)

    # Assert
    assert decoded == original
