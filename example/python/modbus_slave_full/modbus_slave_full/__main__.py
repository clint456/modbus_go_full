"""主入口点。

启动 Modbus TCP/RTU 服务器。
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from .config import Config
from .datastore import ModbusDataStore
from .protocol import ModbusHandler, ModbusRTUServer, ModbusTCPServer
from .utils import setup_logging
from .web import ModbusWebServer

logger = logging.getLogger(__name__)


class ModbusServerApp:
    """Modbus 服务器应用。"""

    def __init__(self, config: Config):
        """初始化应用。

        Args:
            config: 配置对象
        """
        self.config = config
        self.datastore = None
        self.handler = None
        self.tcp_server = None
        self.rtu_server = None
        self.web_server = None
        self.tasks = []
        self.running = False

    async def start(self) -> None:
        """启动服务器。"""
        self.running = True

        # 初始化数据存储
        data_file = Path(self.config.data.data_file) if self.config.data.data_file else None
        self.datastore = ModbusDataStore(
            data_file=data_file, history_max_size=self.config.data.history_max_size
        )

        # 初始化从站
        for slave in self.config.slaves:
            self.datastore.initialize_slave(
                slave.id,
                slave.coils,
                slave.discrete_inputs,
                slave.holding_registers,
                slave.input_registers,
            )

        # 加载数据文件
        await self.datastore.load_from_file()

        # 初始化处理器
        self.handler = ModbusHandler(self.datastore)

        # 启动 TCP 服务器
        if self.config.server.tcp.enabled:
            self.tcp_server = ModbusTCPServer(
                self.handler, self.config.server.tcp.host, self.config.server.tcp.port
            )
            task = asyncio.create_task(self.tcp_server.start())
            self.tasks.append(task)

        # 启动 RTU 服务器
        if self.config.server.rtu.enabled:
            try:
                self.rtu_server = ModbusRTUServer(
                    self.handler,
                    self.config.server.rtu.port,
                    self.config.server.rtu.baudrate,
                    self.config.server.rtu.bytesize,
                    self.config.server.rtu.parity,
                    self.config.server.rtu.stopbits,
                    self.config.server.rtu.timeout,
                )
                task = asyncio.create_task(self.rtu_server.start())
                self.tasks.append(task)
            except ImportError as e:
                logger.warning(f"RTU 服务器启动失败: {e}")

        # 启动 Web 服务器
        if self.config.web.enabled:
            self.web_server = ModbusWebServer(self.datastore, self.handler, self.config.web)
            task = asyncio.create_task(self.web_server.start())
            self.tasks.append(task)

        # 启动自动保存任务
        if self.config.data.auto_save:
            task = asyncio.create_task(self._auto_save_loop())
            self.tasks.append(task)

        logger.info("Modbus 服务器启动完成")

        # 等待任务
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("任务被取消")

    async def stop(self) -> None:
        """停止服务器。"""
        if not self.running:
            return

        self.running = False
        logger.info("正在关闭服务器...")

        # 取消所有任务
        for task in self.tasks:
            task.cancel()

        # 停止服务器
        if self.tcp_server:
            await self.tcp_server.stop()
        if self.rtu_server:
            await self.rtu_server.stop()
        if self.web_server:
            await self.web_server.stop()

        # 保存数据
        if self.datastore:
            await self.datastore.save_to_file()

        logger.info("服务器已关闭")

    async def _auto_save_loop(self) -> None:
        """自动保存循环。"""
        interval = self.config.data.save_interval
        while self.running:
            await asyncio.sleep(interval)
            if self.running:
                await self.datastore.save_to_file()


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Modbus TCP/RTU 服务器")
    parser.add_argument(
        "--config", "-c", type=str, default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    return parser.parse_args()


def main():
    """主函数。"""
    args = parse_args()

    if args.version:
        from . import __version__

        print(f"Modbus Server v{__version__}")
        sys.exit(0)

    # 加载配置
    config_path = Path(args.config)
    if config_path.exists():
        try:
            config = Config.from_yaml(config_path)
            logger.info(f"已加载配置文件: {config_path}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            print("使用默认配置")
            config = Config.get_default()
    else:
        print(f"配置文件不存在: {config_path}")
        print("使用默认配置")
        config = Config.get_default()

        # 创建示例配置文件
        example_config = Path("config.example.yaml")
        if not example_config.exists():
            config.to_yaml(example_config)
            print(f"已创建示例配置文件: {example_config}")

    # 设置日志
    setup_logging(
        level=config.logging.level,
        log_file=config.logging.file,
        max_size=config.logging.max_size,
        backup_count=config.logging.backup_count,
    )

    # 创建应用
    app = ModbusServerApp(config)

    # 设置信号处理
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("收到停止信号")
        asyncio.create_task(app.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # 运行应用
    try:
        loop.run_until_complete(app.start())
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        loop.run_until_complete(app.stop())
        loop.close()


if __name__ == "__main__":
    main()
