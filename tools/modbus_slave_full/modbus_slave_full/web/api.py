"""Web API 路由。

提供 REST API 用于管理 Modbus 服务器。
"""

import json
import logging
from typing import Any, Dict

from aiohttp import web

logger = logging.getLogger(__name__)


class ModbusAPI:
    """Modbus Web API。"""

    def __init__(self, datastore, handler, auth_config):
        """初始化 API。

        Args:
            datastore: 数据存储
            handler: Modbus 处理器
            auth_config: 认证配置
        """
        self.datastore = datastore
        self.handler = handler
        self.auth_config = auth_config

    def setup_routes(self, app: web.Application) -> None:
        """设置路由。

        Args:
            app: aiohttp 应用
        """
        app.router.add_get("/api/slaves", self.get_slaves)
        app.router.add_get("/api/data", self.get_data)
        app.router.add_get("/api/history", self.get_history)
        app.router.add_get("/api/stats", self.get_stats)
        app.router.add_post("/api/write/coil", self.write_coil)
        app.router.add_post("/api/write/register", self.write_register)
        app.router.add_post("/api/write/string", self.write_string)
        app.router.add_get("/api/read/string", self.read_string)
        app.router.add_get("/api/config", self.get_config)
        app.router.add_post("/api/config/resize", self.resize_slave)
        app.router.add_get("/health", self.health_check)

    async def get_slaves(self, request: web.Request) -> web.Response:
        """获取从站列表。"""
        slaves = list(self.datastore.slaves.keys())
        return web.json_response({"slaves": slaves})

    async def get_data(self, request: web.Request) -> web.Response:
        """获取所有数据。"""
        slave_id = request.query.get("slave_id")
        if slave_id:
            try:
                slave_id = int(slave_id)
                slave = self.datastore.get_slave(slave_id)
                if not slave:
                    return web.json_response({"error": "从站不存在"}, status=404)

                data = {
                    "slave_id": slave_id,
                    "coils": slave.coils[:],
                    "discrete_inputs": slave.discrete_inputs[:],
                    "holding_registers": slave.holding_registers[:],
                    "input_registers": slave.input_registers[:],
                }
                return web.json_response(data)
            except ValueError:
                return web.json_response({"error": "无效的从站ID"}, status=400)
        else:
            all_data = self.datastore.get_all_data()
            return web.json_response(all_data)

    async def get_history(self, request: web.Request) -> web.Response:
        """获取历史记录。"""
        limit = int(request.query.get("limit", 100))
        history = self.datastore.get_history(limit)
        return web.json_response({"history": history})

    async def get_stats(self, request: web.Request) -> web.Response:
        """获取统计信息。"""
        stats = self.handler.get_stats()
        return web.json_response(stats)

    async def write_coil(self, request: web.Request) -> web.Response:
        """写入线圈。"""
        try:
            data = await request.json()
            slave_id = data.get("slave_id")
            address = data.get("address")
            value = data.get("value")

            if slave_id is None or address is None or value is None:
                return web.json_response({"error": "缺少参数"}, status=400)

            success = await self.datastore.write_coil(slave_id, address, bool(value), "web")
            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"error": "写入失败"}, status=400)
        except Exception as e:
            logger.error(f"写入线圈错误: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def write_register(self, request: web.Request) -> web.Response:
        """写入寄存器。"""
        try:
            data = await request.json()
            slave_id = data.get("slave_id")
            address = data.get("address")
            value = data.get("value")

            if slave_id is None or address is None or value is None:
                return web.json_response({"error": "缺少参数"}, status=400)

            success = await self.datastore.write_register(slave_id, address, int(value), "web")
            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"error": "写入失败"}, status=400)
        except Exception as e:
            logger.error(f"写入寄存器错误: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def write_string(self, request: web.Request) -> web.Response:
        """写入字符串到寄存器。
        
        字符串编码方式：每个寄存器存储2个ASCII字符
        高字节存储第一个字符，低字节存储第二个字符
        """
        try:
            data = await request.json()
            slave_id = data.get("slave_id")
            address = data.get("address")
            text = data.get("text", "")
            
            if slave_id is None or address is None:
                return web.json_response({"error": "缺少参数"}, status=400)
            
            # 将字符串转换为寄存器值
            # 每个寄存器存储2个字符：高字节=第1个字符，低字节=第2个字符
            registers = []
            for i in range(0, len(text), 2):
                char1 = ord(text[i]) if i < len(text) else 0
                char2 = ord(text[i + 1]) if i + 1 < len(text) else 0
                # 高字节 << 8 | 低字节
                register_value = (char1 << 8) | char2
                registers.append(register_value)
            
            # 写入所有寄存器
            for i, value in enumerate(registers):
                success = await self.datastore.write_register(
                    slave_id, address + i, value, "web"
                )
                if not success:
                    return web.json_response(
                        {"error": f"写入地址 {address + i} 失败"}, status=400
                    )
            
            return web.json_response({
                "success": True,
                "registers_written": len(registers),
                "text_length": len(text),
                "address_range": f"{address}-{address + len(registers) - 1}"
            })
            
        except Exception as e:
            logger.error(f"写入字符串错误: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def read_string(self, request: web.Request) -> web.Response:
        """从寄存器读取字符串。"""
        try:
            slave_id = int(request.query.get("slave_id"))
            address = int(request.query.get("address"))
            # 支持 length 或 count 参数
            length = int(request.query.get("count", request.query.get("length", 10)))  # 默认读取10个寄存器
            
            slave = self.datastore.get_slave(slave_id)
            if not slave:
                return web.json_response({"error": "从站不存在"}, status=404)
            
            # 读取寄存器
            registers = []
            for i in range(length):
                if address + i < len(slave.holding_registers):
                    registers.append(slave.holding_registers[address + i])
                else:
                    registers.append(0)
            
            # 将寄存器转换为字符串
            text = ""
            for reg in registers:
                # 高字节
                char1 = (reg >> 8) & 0xFF
                # 低字节
                char2 = reg & 0xFF
                
                if char1 != 0:  # 忽略空字符
                    text += chr(char1)
                if char2 != 0:  # 忽略空字符
                    text += chr(char2)
            
            return web.json_response({
                "text": text,
                "registers": registers,
                "length": len(text),
                "address_range": f"{address}-{address + length - 1}"
            })
            
        except Exception as e:
            logger.error(f"读取字符串错误: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_config(self, request: web.Request) -> web.Response:
        """获取从站配置信息。"""
        try:
            slave_id = request.query.get("slave_id")
            
            if slave_id:
                slave_id = int(slave_id)
                slave = self.datastore.get_slave(slave_id)
                if not slave:
                    return web.json_response({"error": "从站不存在"}, status=404)
                
                return web.json_response({
                    "slave_id": slave_id,
                    "coils": len(slave.coils),
                    "discrete_inputs": len(slave.discrete_inputs),
                    "holding_registers": len(slave.holding_registers),
                    "input_registers": len(slave.input_registers)
                })
            else:
                # 返回所有从站的配置
                configs = {}
                for sid, slave in self.datastore.slaves.items():
                    configs[sid] = {
                        "coils": len(slave.coils),
                        "discrete_inputs": len(slave.discrete_inputs),
                        "holding_registers": len(slave.holding_registers),
                        "input_registers": len(slave.input_registers)
                    }
                return web.json_response({"slaves": configs})
                
        except Exception as e:
            logger.error(f"获取配置错误: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def resize_slave(self, request: web.Request) -> web.Response:
        """动态调整从站数据块大小。"""
        try:
            data = await request.json()
            slave_id = data.get("slave_id")
            coils = data.get("coils")
            discrete_inputs = data.get("discrete_inputs")
            holding_registers = data.get("holding_registers")
            input_registers = data.get("input_registers")
            
            if slave_id is None:
                return web.json_response({"error": "缺少从站ID"}, status=400)
            
            # 验证参数
            if coils is not None and (coils < 0 or coils > 65536):
                return web.json_response({"error": "线圈数量无效 (0-65536)"}, status=400)
            if discrete_inputs is not None and (discrete_inputs < 0 or discrete_inputs > 65536):
                return web.json_response({"error": "离散输入数量无效 (0-65536)"}, status=400)
            if holding_registers is not None and (holding_registers < 0 or holding_registers > 65536):
                return web.json_response({"error": "保持寄存器数量无效 (0-65536)"}, status=400)
            if input_registers is not None and (input_registers < 0 or input_registers > 65536):
                return web.json_response({"error": "输入寄存器数量无效 (0-65536)"}, status=400)
            
            success = self.datastore.resize_slave(
                slave_id, coils, discrete_inputs, holding_registers, input_registers
            )
            
            if success:
                # 获取调整后的配置
                slave = self.datastore.get_slave(slave_id)
                return web.json_response({
                    "success": True,
                    "slave_id": slave_id,
                    "new_config": {
                        "coils": len(slave.coils),
                        "discrete_inputs": len(slave.discrete_inputs),
                        "holding_registers": len(slave.holding_registers),
                        "input_registers": len(slave.input_registers)
                    }
                })
            else:
                return web.json_response({"error": "调整失败，从站不存在"}, status=404)
                
        except Exception as e:
            logger.error(f"调整大小错误: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def health_check(self, request: web.Request) -> web.Response:
        """健康检查。"""
        return web.json_response({"status": "ok"})
