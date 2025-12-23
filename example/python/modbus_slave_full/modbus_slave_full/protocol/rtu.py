"""Modbus RTU 服务器。

实现 Modbus RTU 协议服务器，通过串口通信。
"""

import asyncio
import logging
from typing import Optional

try:
    import serial_asyncio
except ImportError:
    serial_asyncio = None

from .handlers import ModbusHandler
from .utils import add_crc16, verify_crc16

logger = logging.getLogger(__name__)


class ModbusRTUServer:
    """Modbus RTU 服务器。"""

    def __init__(
        self,
        handler: ModbusHandler,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 1.0,
    ):
        """初始化 RTU 服务器。

        Args:
            handler: Modbus 处理器
            port: 串口端口
            baudrate: 波特率
            bytesize: 数据位
            parity: 校验位 ('N', 'E', 'O')
            stopbits: 停止位
            timeout: 超时时间
        """
        if serial_asyncio is None:
            raise ImportError("需要安装 pyserial-asyncio: pip install pyserial-asyncio")

        self.handler = handler
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.running = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def start(self) -> None:
        """启动 RTU 服务器。"""
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
            )
            self.running = True
            logger.info(
                f"Modbus RTU 服务器启动: {self.port} "
                f"({self.baudrate},{self.bytesize}{self.parity}{self.stopbits})"
            )

            await self._process_frames()

        except Exception as e:
            logger.error(f"启动 RTU 服务器失败: {e}")
            raise

    async def stop(self) -> None:
        """停止 RTU 服务器。"""
        self.running = False
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass
        logger.info("Modbus RTU 服务器已停止")

    async def _process_frames(self) -> None:
        """处理 RTU 帧。"""
        buffer = bytearray()
        idle_timeout = 0.05  # 50ms 帧间隔

        while self.running:
            try:
                # 读取数据
                chunk = await asyncio.wait_for(self.reader.read(256), timeout=idle_timeout)
                if chunk:
                    buffer.extend(chunk)
                    continue

            except asyncio.TimeoutError:
                # 超时，处理缓冲区中的帧
                if len(buffer) >= 4:  # 最小帧长度: slave_id(1) + fc(1) + crc(2)
                    await self._handle_frame(bytes(buffer))
                buffer.clear()
                continue

            except Exception as e:
                logger.error(f"读取串口数据错误: {e}")
                await asyncio.sleep(0.1)
                continue

    async def _handle_frame(self, frame: bytes) -> None:
        """处理单个 RTU 帧。

        Args:
            frame: 完整的 RTU 帧
        """
        if len(frame) < 4:
            logger.warning(f"RTU 帧太短: {len(frame)} 字节")
            return

        # 验证 CRC
        if not verify_crc16(frame):
            logger.warning(f"RTU CRC 校验失败")
            return

        # 解析帧
        slave_id = frame[0]
        function_code = frame[1]
        data = frame[2:-2]  # 去掉 slave_id, fc 和 CRC

        logger.debug(
            f"RTU 请求: 从站={slave_id}, FC={function_code:02X}, 数据长度={len(data)}"
        )

        # 处理请求
        response = await self.handler.handle_request(slave_id, function_code, data, "rtu")

        if response:
            # 构建响应帧
            response_frame = bytes([slave_id]) + response
            response_frame = add_crc16(response_frame)

            # 发送响应
            self.writer.write(response_frame)
            await self.writer.drain()
            logger.debug(f"RTU 响应发送, 长度={len(response_frame)}")
        else:
            logger.error(f"处理 RTU 请求失败")
