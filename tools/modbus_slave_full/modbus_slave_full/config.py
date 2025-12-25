"""配置管理模块。

此模块负责加载和管理服务器配置，支持从 YAML 文件读取配置。
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class TCPConfig:
    """TCP 服务器配置。"""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 5020


@dataclass
class RTUConfig:
    """RTU 串口服务器配置。"""

    enabled: bool = True
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: float = 1.0


@dataclass
class ServerConfig:
    """服务器配置。"""

    tcp: TCPConfig = field(default_factory=TCPConfig)
    rtu: RTUConfig = field(default_factory=RTUConfig)


@dataclass
class SlaveConfig:
    """从站配置。"""

    id: int
    name: str = "设备"
    coils: int = 100
    discrete_inputs: int = 100
    holding_registers: int = 100
    input_registers: int = 100


@dataclass
class WebAuthConfig:
    """Web 认证配置。"""

    enabled: bool = True
    username: str = "admin"
    password: str = "admin123"


@dataclass
class WebConfig:
    """Web 服务器配置。"""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    auth: WebAuthConfig = field(default_factory=WebAuthConfig)


@dataclass
class DataConfig:
    """数据管理配置。"""

    auto_save: bool = True
    save_interval: int = 60
    data_file: str = "modbus_data.json"
    history_enabled: bool = True
    history_max_size: int = 1000


@dataclass
class LoggingConfig:
    """日志配置。"""

    level: str = "INFO"
    file: Optional[str] = "modbus_server.log"
    max_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class Config:
    """完整配置。"""

    server: ServerConfig = field(default_factory=ServerConfig)
    slaves: List[SlaveConfig] = field(default_factory=list)
    web: WebConfig = field(default_factory=WebConfig)
    data: DataConfig = field(default_factory=DataConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """从 YAML 文件加载配置。

        Args:
            path: 配置文件路径

        Returns:
            Config 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML 解析错误
        """
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            data = {}

        # 解析服务器配置
        server_data = data.get("server", {})
        tcp_config = TCPConfig(**server_data.get("tcp", {}))
        rtu_config = RTUConfig(**server_data.get("rtu", {}))
        server_config = ServerConfig(tcp=tcp_config, rtu=rtu_config)

        # 解析从站配置
        slaves_data = data.get("slaves", [])
        if not slaves_data:
            slaves_data = [{"id": 1, "name": "主设备"}]
        slaves = [SlaveConfig(**slave) for slave in slaves_data]

        # 解析 Web 配置
        web_data = data.get("web", {})
        auth_data = web_data.get("auth", {})
        web_auth = WebAuthConfig(**auth_data)
        web_config = WebConfig(**{k: v for k, v in web_data.items() if k != "auth"})
        web_config.auth = web_auth

        # 解析数据配置
        data_config = DataConfig(**data.get("data", {}))

        # 解析日志配置
        logging_config = LoggingConfig(**data.get("logging", {}))

        return cls(
            server=server_config,
            slaves=slaves,
            web=web_config,
            data=data_config,
            logging=logging_config,
        )

    @classmethod
    def get_default(cls) -> "Config":
        """获取默认配置。

        Returns:
            默认 Config 实例
        """
        return cls(
            slaves=[SlaveConfig(id=1, name="主设备")],
        )

    def to_yaml(self, path: Path) -> None:
        """将配置保存到 YAML 文件。

        Args:
            path: 目标文件路径
        """
        data = {
            "server": {
                "tcp": {
                    "enabled": self.server.tcp.enabled,
                    "host": self.server.tcp.host,
                    "port": self.server.tcp.port,
                },
                "rtu": {
                    "enabled": self.server.rtu.enabled,
                    "port": self.server.rtu.port,
                    "baudrate": self.server.rtu.baudrate,
                    "bytesize": self.server.rtu.bytesize,
                    "parity": self.server.rtu.parity,
                    "stopbits": self.server.rtu.stopbits,
                    "timeout": self.server.rtu.timeout,
                },
            },
            "slaves": [
                {
                    "id": slave.id,
                    "name": slave.name,
                    "coils": slave.coils,
                    "discrete_inputs": slave.discrete_inputs,
                    "holding_registers": slave.holding_registers,
                    "input_registers": slave.input_registers,
                }
                for slave in self.slaves
            ],
            "web": {
                "enabled": self.web.enabled,
                "host": self.web.host,
                "port": self.web.port,
                "auth": {
                    "enabled": self.web.auth.enabled,
                    "username": self.web.auth.username,
                    "password": self.web.auth.password,
                },
            },
            "data": {
                "auto_save": self.data.auto_save,
                "save_interval": self.data.save_interval,
                "data_file": self.data.data_file,
                "history_enabled": self.data.history_enabled,
                "history_max_size": self.data.history_max_size,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "max_size": self.logging.max_size,
                "backup_count": self.logging.backup_count,
            },
        }

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
