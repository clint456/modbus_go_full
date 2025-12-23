"""Modbus TCP 服务器。

实现 Modbus TCP 协议服务器。
"""

import asyncio
import logging
import struct
from typing import Optional

from .handlers import ModbusHandler
from .utils import build_mbap_header, parse_mbap_header

logger = logging.getLogger(__name__)


class ModbusTCPServer:
    """Modbus TCP 服务器。"""

    def __init__(self, handler: ModbusHandler, host: str = "0.0.0.0", port: int = 5020):
        """初始化 TCP 服务器。

        Args:
            handler: Modbus 处理器
            host: 监听地址
            port: 监听端口
        """
        self.handler = handler
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.clients = set()

    async def start(self) -> None:
        """启动服务器。"""
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"Modbus TCP 服务器启动: {self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        """停止服务器。"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Modbus TCP 服务器已停止")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """处理客户端连接。

        Args:
            reader: 流读取器
            writer: 流写入器
        """
        addr = writer.get_extra_info("peername")
        logger.info(f"客户端连接: {addr}")
        self.clients.add(writer)

        try:
            while True:
                # 读取 MBAP 头部（7字节）
                header = await reader.readexactly(7)
                if not header:
                    break

                parsed = parse_mbap_header(header)
                if not parsed:
                    logger.warning(f"无效的 MBAP 头部来自 {addr}")
                    break

                transaction_id, protocol_id, length, unit_id = parsed

                if protocol_id != 0:
                    logger.warning(f"无效的协议ID {protocol_id} 来自 {addr}")
                    break

                # 读取 PDU
                pdu = await reader.readexactly(length - 1)
                if len(pdu) < 1:
                    logger.warning(f"PDU太短来自 {addr}")
                    break

                function_code = pdu[0]
                data = pdu[1:]

                logger.debug(
                    f"TCP 请求来自 {addr}: 从站={unit_id}, FC={function_code:02X}, "
                    f"数据长度={len(data)}"
                )

                # 处理请求
                response = await self.handler.handle_request(
                    unit_id, function_code, data, "tcp"
                )

                if response:
                    # 构建响应
                    response_header = build_mbap_header(
                        transaction_id, unit_id, len(response) + 1
                    )
                    writer.write(response_header + response)
                    await writer.drain()
                    logger.debug(f"TCP 响应发送到 {addr}, 长度={len(response)}")
                else:
                    logger.error(f"处理请求失败来自 {addr}")

        except asyncio.IncompleteReadError:
            logger.info(f"客户端断开连接: {addr}")
        except ConnectionResetError:
            logger.info(f"客户端连接重置: {addr}")
        except Exception as e:
            logger.error(f"处理客户端错误 {addr}: {e}")
        finally:
            self.clients.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"客户端连接关闭: {addr}")
