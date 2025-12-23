"""协议工具模块。

包含 CRC16 校验、帧解析等工具函数。
"""

import struct
from typing import List, Optional, Tuple


def calculate_crc16(data: bytes) -> int:
    """计算 CRC16-Modbus 校验码。

    Args:
        data: 要校验的数据

    Returns:
        CRC16 值
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def verify_crc16(frame: bytes) -> bool:
    """验证 RTU 帧的 CRC16。

    Args:
        frame: 完整的 RTU 帧（包含 CRC）

    Returns:
        CRC 是否正确
    """
    if len(frame) < 4:
        return False
    data = frame[:-2]
    crc_received = struct.unpack("<H", frame[-2:])[0]
    crc_calculated = calculate_crc16(data)
    return crc_received == crc_calculated


def add_crc16(data: bytes) -> bytes:
    """为数据添加 CRC16。

    Args:
        data: 原始数据

    Returns:
        添加了 CRC16 的数据
    """
    crc = calculate_crc16(data)
    return data + struct.pack("<H", crc)


def parse_mbap_header(header: bytes) -> Optional[Tuple[int, int, int, int]]:
    """解析 MBAP 头部。

    Args:
        header: MBAP 头部（7字节）

    Returns:
        (transaction_id, protocol_id, length, unit_id) 或 None
    """
    if len(header) != 7:
        return None
    transaction_id, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
    return transaction_id, protocol_id, length, unit_id


def build_mbap_header(transaction_id: int, unit_id: int, length: int) -> bytes:
    """构建 MBAP 头部。

    Args:
        transaction_id: 事务ID
        unit_id: 单元ID
        length: PDU长度+1

    Returns:
        MBAP 头部（7字节）
    """
    return struct.pack(">HHHB", transaction_id, 0, length, unit_id)


def bytes_to_bits(data: bytes, count: int) -> List[bool]:
    """将字节数组转换为位列表。

    Args:
        data: 字节数组
        count: 位数量

    Returns:
        位列表
    """
    bits = []
    for byte in data:
        for i in range(8):
            if len(bits) >= count:
                break
            bits.append(bool((byte >> i) & 1))
        if len(bits) >= count:
            break
    return bits


def bits_to_bytes(bits: List[bool]) -> bytes:
    """将位列表转换为字节数组。

    Args:
        bits: 位列表

    Returns:
        字节数组
    """
    byte_count = (len(bits) + 7) // 8
    result = bytearray(byte_count)
    for i, bit in enumerate(bits):
        if bit:
            byte_index = i // 8
            bit_index = i % 8
            result[byte_index] |= 1 << bit_index
    return bytes(result)


def words_to_bytes(words: List[int]) -> bytes:
    """将寄存器值列表转换为字节数组。

    Args:
        words: 寄存器值列表（16位）

    Returns:
        字节数组
    """
    return b"".join(struct.pack(">H", word & 0xFFFF) for word in words)


def bytes_to_words(data: bytes) -> List[int]:
    """将字节数组转换为寄存器值列表。

    Args:
        data: 字节数组

    Returns:
        寄存器值列表（16位）
    """
    if len(data) % 2 != 0:
        return []
    return [struct.unpack(">H", data[i : i + 2])[0] for i in range(0, len(data), 2)]
