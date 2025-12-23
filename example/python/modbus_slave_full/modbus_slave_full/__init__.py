"""主模块包初始化文件。"""

__version__ = "1.0.0"
__author__ = "clint"

from .config import Config
from .datastore import ModbusDataStore

__all__ = ["Config", "ModbusDataStore", "__version__"]
