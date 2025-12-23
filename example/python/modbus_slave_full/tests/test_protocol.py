"""协议工具测试。"""

import pytest

from modbus_slave_full.protocol.utils import (
    add_crc16,
    bits_to_bytes,
    bytes_to_bits,
    bytes_to_words,
    calculate_crc16,
    verify_crc16,
    words_to_bytes,
)


def test_calculate_crc16():
    """测试 CRC16 计算。"""
    data = b"\x01\x03\x00\x00\x00\x0A"
    crc = calculate_crc16(data)
    # Modbus CRC16 结果（小端序）
    assert crc == 0xCDC5


def test_verify_crc16():
    """测试 CRC16 验证。"""
    # CRC 字节以小端序存储: C5 CD (低字节在前)
    frame = b"\x01\x03\x00\x00\x00\x0A\xC5\xCD"
    assert verify_crc16(frame) is True

    invalid_frame = b"\x01\x03\x00\x00\x00\x0A\x00\x00"
    assert verify_crc16(invalid_frame) is False


def test_add_crc16():
    """测试添加 CRC16。"""
    data = b"\x01\x03\x00\x00\x00\x0A"
    frame = add_crc16(data)
    assert frame == b"\x01\x03\x00\x00\x00\x0A\xC5\xCD"


def test_bits_to_bytes():
    """测试位转字节。"""
    bits = [True, False, True, False, False, False, False, False]
    data = bits_to_bytes(bits)
    assert data == b"\x05"


def test_bytes_to_bits():
    """测试字节转位。"""
    data = b"\x05"
    bits = bytes_to_bits(data, 8)
    assert bits == [True, False, True, False, False, False, False, False]


def test_words_to_bytes():
    """测试字转字节。"""
    words = [0x1234, 0x5678]
    data = words_to_bytes(words)
    assert data == b"\x12\x34\x56\x78"


def test_bytes_to_words():
    """测试字节转字。"""
    data = b"\x12\x34\x56\x78"
    words = bytes_to_words(data)
    assert words == [0x1234, 0x5678]
