"""测试新增的功能码。"""

import asyncio
import pytest

from modbus_slave_full.datastore import ModbusDataStore
from modbus_slave_full.protocol.handlers import ModbusHandler


@pytest.fixture
async def setup():
    """设置测试环境。"""
    datastore = ModbusDataStore()
    # 增加寄存器数量以支持文件记录功能（需要更大的地址空间）
    datastore.initialize_slave(1, coils=100, holding_registers=50000)
    handler = ModbusHandler(datastore)
    return handler, datastore


@pytest.mark.asyncio
async def test_read_exception_status(setup):
    """测试读异常状态 (FC07)。"""
    handler, datastore = setup
    response = await handler.handle_request(1, 0x07, b"", "test")
    assert response is not None
    assert response[0] == 0x07
    assert len(response) == 2


@pytest.mark.asyncio
async def test_diagnostics(setup):
    """测试诊断 (FC08)。"""
    handler, datastore = setup
    # 子功能 0x0000: 返回查询数据
    data = b"\x00\x00\x12\x34"
    response = await handler.handle_request(1, 0x08, data, "test")
    assert response is not None
    assert response[0] == 0x08
    assert response[1:] == data


@pytest.mark.asyncio
async def test_get_comm_event_counter(setup):
    """测试获取通信事件计数器 (FC11)。"""
    handler, datastore = setup
    response = await handler.handle_request(1, 0x0B, b"", "test")
    assert response is not None
    assert response[0] == 0x0B
    assert len(response) == 5


@pytest.mark.asyncio
async def test_get_comm_event_log(setup):
    """测试获取通信事件日志 (FC12)。"""
    handler, datastore = setup
    response = await handler.handle_request(1, 0x0C, b"", "test")
    assert response is not None
    assert response[0] == 0x0C
    assert len(response) >= 7


@pytest.mark.asyncio
async def test_report_slave_id(setup):
    """测试报告从站ID (FC17)。"""
    handler, datastore = setup
    response = await handler.handle_request(1, 0x11, b"", "test")
    assert response is not None
    assert response[0] == 0x11
    assert len(response) >= 3
    # 检查运行指示符
    assert response[-1] == 0xFF


@pytest.mark.asyncio
async def test_mask_write_register(setup):
    """测试屏蔽写寄存器 (FC22)。"""
    handler, datastore = setup
    
    # 先写入一个初始值
    await datastore.write_register(1, 5, 0x12, "test")
    
    # 屏蔽写: AND=0xF2, OR=0x25
    # 结果 = (0x12 & 0xF2) | (0x25 & ~0xF2) = 0x12 | 0x05 = 0x17
    import struct
    data = struct.pack(">HHH", 5, 0x00F2, 0x0025)
    response = await handler.handle_request(1, 0x16, data, "test")
    
    assert response is not None
    assert response[0] == 0x16
    
    # 验证值
    values = await datastore.read_holding_registers(1, 5, 1)
    expected = (0x12 & 0x00F2) | (0x0025 & (~0x00F2 & 0xFFFF))
    assert values[0] == expected


@pytest.mark.asyncio
async def test_read_fifo_queue(setup):
    """测试读FIFO队列 (FC24)。"""
    handler, datastore = setup
    
    # 设置FIFO: 地址100存储计数，地址101-105存储数据
    await datastore.write_register(1, 100, 5, "test")  # 5个值
    await datastore.write_registers(1, 101, [10, 20, 30, 40, 50], "test")
    
    import struct
    data = struct.pack(">H", 100)
    response = await handler.handle_request(1, 0x18, data, "test")
    
    assert response is not None
    assert response[0] == 0x18
    # 应该返回: FC + byte_count(2字节) + FIFO_count(2字节) + values
    assert len(response) >= 5


@pytest.mark.asyncio
async def test_read_file_record(setup):
    """测试读文件记录 (FC20)。"""
    handler, datastore = setup
    
    # 写入一些测试数据到寄存器
    await datastore.write_registers(1, 100, [1, 2, 3, 4, 5], "test")
    
    # 构建请求: byte_count(1) + [ref_type(1) + file_number(2) + record_number(2) + record_length(2)]
    import struct
    # byte_count=7, 然后是子请求
    request = bytes([7]) + struct.pack(">BHHH", 0x06, 0, 100, 5)
    response = await handler.handle_request(1, 0x14, request, "test")
    
    assert response is not None
    assert response[0] == 0x14


@pytest.mark.asyncio
async def test_write_file_record(setup):
    """测试写文件记录 (FC21)。"""
    handler, datastore = setup
    
    # 构建请求: byte_count(1) + [ref_type(1) + file_number(2) + record_number(2) + record_length(2) + data]
    import struct
    values = [100, 200, 300]
    byte_count = 7 + len(values) * 2
    request = bytes([byte_count]) + struct.pack(">BHHH", 0x06, 0, 50, len(values))
    for val in values:
        request += struct.pack(">H", val)
    
    response = await handler.handle_request(1, 0x15, request, "test")
    
    assert response is not None
    assert response[0] == 0x15
    
    # 验证写入的数据
    result = await datastore.read_holding_registers(1, 50, len(values))
    assert result == values


@pytest.mark.asyncio
async def test_function_code_statistics(setup):
    """测试功能码统计。"""
    handler, datastore = setup
    
    # 执行几个不同的请求
    await handler.handle_request(1, 0x01, b"\x00\x00\x00\x0A", "test")  # FC01
    await handler.handle_request(1, 0x03, b"\x00\x00\x00\x0A", "test")  # FC03
    await handler.handle_request(1, 0x07, b"", "test")  # FC07
    await handler.handle_request(1, 0x11, b"", "test")  # FC17
    
    stats = handler.get_stats()
    assert stats["total_requests"] >= 4
    assert "FC01" in stats["function_codes"]
    assert "FC03" in stats["function_codes"]
    assert "FC07" in stats["function_codes"]
    assert "FC17" in stats["function_codes"]
