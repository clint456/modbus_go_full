"""数据存储测试。"""

import asyncio
from pathlib import Path

import pytest

from modbus_slave_full.datastore import ModbusDataStore


@pytest.fixture
def datastore():
    """创建数据存储实例。"""
    ds = ModbusDataStore()
    ds.initialize_slave(1, coils=10, holding_registers=10)
    return ds


@pytest.mark.asyncio
async def test_read_coils(datastore):
    """测试读取线圈。"""
    values = await datastore.read_coils(1, 0, 5)
    assert values is not None
    assert len(values) == 5
    assert all(v is False for v in values)


@pytest.mark.asyncio
async def test_write_coil(datastore):
    """测试写入线圈。"""
    success = await datastore.write_coil(1, 0, True, "test")
    assert success is True

    values = await datastore.read_coils(1, 0, 1)
    assert values == [True]


@pytest.mark.asyncio
async def test_write_coils(datastore):
    """测试写入多个线圈。"""
    success = await datastore.write_coils(1, 0, [True, False, True], "test")
    assert success is True

    values = await datastore.read_coils(1, 0, 3)
    assert values == [True, False, True]


@pytest.mark.asyncio
async def test_read_holding_registers(datastore):
    """测试读取保持寄存器。"""
    values = await datastore.read_holding_registers(1, 0, 5)
    assert values is not None
    assert len(values) == 5
    assert all(v == 0 for v in values)


@pytest.mark.asyncio
async def test_write_register(datastore):
    """测试写入寄存器。"""
    success = await datastore.write_register(1, 0, 1234, "test")
    assert success is True

    values = await datastore.read_holding_registers(1, 0, 1)
    assert values == [1234]


@pytest.mark.asyncio
async def test_write_registers(datastore):
    """测试写入多个寄存器。"""
    success = await datastore.write_registers(1, 0, [100, 200, 300], "test")
    assert success is True

    values = await datastore.read_holding_registers(1, 0, 3)
    assert values == [100, 200, 300]


@pytest.mark.asyncio
async def test_history(datastore):
    """测试历史记录。"""
    await datastore.write_coil(1, 0, True, "test")
    await datastore.write_register(1, 0, 100, "test")

    history = datastore.get_history()
    assert len(history) >= 2


@pytest.mark.asyncio
async def test_invalid_slave_id(datastore):
    """测试无效的从站ID。"""
    values = await datastore.read_coils(99, 0, 5)
    assert values is None


@pytest.mark.asyncio
async def test_invalid_address(datastore):
    """测试无效的地址。"""
    values = await datastore.read_coils(1, 100, 5)
    assert values is None
