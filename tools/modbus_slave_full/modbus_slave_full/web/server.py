"""Web 服务器。

提供 HTTP 和 WebSocket 服务。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Set

from aiohttp import web
from aiohttp_cors import ResourceOptions, setup as setup_cors

from .api import ModbusAPI

logger = logging.getLogger(__name__)


class ModbusWebServer:
    """Modbus Web 服务器。"""

    def __init__(self, datastore, handler, config):
        """初始化 Web 服务器。

        Args:
            datastore: 数据存储
            handler: Modbus 处理器
            config: Web 配置
        """
        self.datastore = datastore
        self.handler = handler
        self.config = config
        self.app = web.Application()
        self.api = ModbusAPI(datastore, handler, config.auth)
        self.ws_clients: Set[web.WebSocketResponse] = set()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """设置路由。"""
        # API 路由
        self.api.setup_routes(self.app)

        # WebSocket 路由
        self.app.router.add_get("/ws", self.websocket_handler)

        # 静态文件
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.router.add_static("/static/", path=static_dir, name="static")
            self.app.router.add_get("/", self.index_handler)

        # 设置 CORS
        cors = setup_cors(
            self.app,
            defaults={
                "*": ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*",
                )
            },
        )

        # 为所有路由添加 CORS
        for route in list(self.app.router.routes()):
            if not isinstance(route.resource, web.StaticResource):
                cors.add(route)

    async def index_handler(self, request: web.Request) -> web.Response:
        """首页处理器。"""
        static_dir = Path(__file__).parent / "static"
        index_file = static_dir / "index.html"
        if index_file.exists():
            return web.FileResponse(index_file)
        return web.Response(text="Modbus Server Web Interface", status=200)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket 处理器。"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)

        logger.info(f"WebSocket 客户端连接: {request.remote}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_ws_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_json({"error": "无效的 JSON"})
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket 错误: {ws.exception()}")
        finally:
            self.ws_clients.discard(ws)
            logger.info(f"WebSocket 客户端断开: {request.remote}")

        return ws

    async def _handle_ws_message(self, ws: web.WebSocketResponse, data: dict) -> None:
        """处理 WebSocket 消息。"""
        msg_type = data.get("type")

        if msg_type == "subscribe":
            # 订阅数据更新
            await ws.send_json({"type": "subscribed"})
        elif msg_type == "get_data":
            # 获取当前数据
            all_data = self.datastore.get_all_data()
            await ws.send_json({"type": "data", "data": all_data})
        else:
            await ws.send_json({"error": "未知的消息类型"})

    async def broadcast_data_change(self, slave_id: int, data_type: str, address: int) -> None:
        """广播数据变化。

        Args:
            slave_id: 从站ID
            data_type: 数据类型
            address: 地址
        """
        message = {
            "type": "data_change",
            "slave_id": slave_id,
            "data_type": data_type,
            "address": address,
        }

        # 向所有连接的 WebSocket 客户端发送消息
        disconnected = set()
        for ws in self.ws_clients:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)

        # 移除断开的客户端
        self.ws_clients -= disconnected

    async def start(self) -> None:
        """启动 Web 服务器。"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        logger.info(f"Web 服务器启动: http://{self.config.host}:{self.config.port}")

    async def stop(self) -> None:
        """停止 Web 服务器。"""
        await self.app.shutdown()
        await self.app.cleanup()
        logger.info("Web 服务器已停止")
