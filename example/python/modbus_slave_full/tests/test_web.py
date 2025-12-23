"""Web API 测试。"""

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from modbus_slave_full.datastore import ModbusDataStore
from modbus_slave_full.protocol import ModbusHandler
from modbus_slave_full.web.api import ModbusAPI


class TestModbusAPI(AioHTTPTestCase):
    """Web API 测试类。"""

    async def get_application(self):
        """创建测试应用。"""
        # 创建数据存储和处理器
        self.datastore = ModbusDataStore()
        self.datastore.initialize_slave(1, coils=10, holding_registers=10)
        self.handler = ModbusHandler(self.datastore)

        # 创建应用
        app = web.Application()

        # 设置 API
        class MockAuthConfig:
            enabled = False
            username = "admin"
            password = "admin123"

        api = ModbusAPI(self.datastore, self.handler, MockAuthConfig())
        api.setup_routes(app)

        return app

    async def test_get_slaves(self):
        """测试获取从站列表。"""
        resp = await self.client.get("/api/slaves")
        assert resp.status == 200
        data = await resp.json()
        assert "slaves" in data
        assert 1 in data["slaves"]

    async def test_get_data(self):
        """测试获取数据。"""
        resp = await self.client.get("/api/data?slave_id=1")
        assert resp.status == 200
        data = await resp.json()
        assert "coils" in data
        assert "holding_registers" in data

    async def test_write_coil(self):
        """测试写入线圈。"""
        resp = await self.client.post(
            "/api/write/coil", json={"slave_id": 1, "address": 0, "value": True}
        )
        assert resp.status == 200

        # 验证写入
        values = await self.datastore.read_coils(1, 0, 1)
        assert values == [True]

    async def test_write_register(self):
        """测试写入寄存器。"""
        resp = await self.client.post(
            "/api/write/register", json={"slave_id": 1, "address": 0, "value": 1234}
        )
        assert resp.status == 200

        # 验证写入
        values = await self.datastore.read_holding_registers(1, 0, 1)
        assert values == [1234]

    async def test_health_check(self):
        """测试健康检查。"""
        resp = await self.client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
