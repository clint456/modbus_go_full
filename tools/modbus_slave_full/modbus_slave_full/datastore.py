"""数据存储模块。

此模块负责管理 Modbus 数据（线圈、离散输入、保持寄存器、输入寄存器）。
支持多从站ID，数据持久化和历史记录。
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DataBlock:
    """数据块。"""

    coils: List[bool] = field(default_factory=list)
    discrete_inputs: List[bool] = field(default_factory=list)
    holding_registers: List[int] = field(default_factory=list)
    input_registers: List[int] = field(default_factory=list)


@dataclass
class HistoryRecord:
    """历史记录。"""

    timestamp: str
    slave_id: int
    data_type: str  # coils, holding_registers, etc.
    address: int
    old_value: any
    new_value: any
    source: str  # tcp, rtu, web


class ModbusDataStore:
    """Modbus 数据存储。

    管理多个从站的数据，支持数据持久化和历史记录。
    """

    def __init__(self, data_file: Optional[Path] = None, history_max_size: int = 1000):
        """初始化数据存储。

        Args:
            data_file: 数据文件路径
            history_max_size: 历史记录最大数量
        """
        self.data_file = data_file
        self.history_max_size = history_max_size
        self.slaves: Dict[int, DataBlock] = {}
        self.history: List[HistoryRecord] = []
        self._lock = asyncio.Lock()
        self._modified = False

    def initialize_slave(
        self,
        slave_id: int,
        coils: int = 100,
        discrete_inputs: int = 100,
        holding_registers: int = 100,
        input_registers: int = 100,
    ) -> None:
        """初始化从站数据。

        Args:
            slave_id: 从站ID
            coils: 线圈数量
            discrete_inputs: 离散输入数量
            holding_registers: 保持寄存器数量
            input_registers: 输入寄存器数量
        """
        self.slaves[slave_id] = DataBlock(
            coils=[False] * coils,
            discrete_inputs=[False] * discrete_inputs,
            holding_registers=[0] * holding_registers,
            input_registers=[0] * input_registers,
        )
        logger.info(f"初始化从站 {slave_id}: {coils} 线圈, {holding_registers} 寄存器")

    def get_slave(self, slave_id: int) -> Optional[DataBlock]:
        """获取从站数据块。

        Args:
            slave_id: 从站ID

        Returns:
            数据块，如果不存在返回 None
        """
        return self.slaves.get(slave_id)
    
    def resize_slave(self, slave_id: int, coils: Optional[int] = None, 
                     discrete_inputs: Optional[int] = None,
                     holding_registers: Optional[int] = None,
                     input_registers: Optional[int] = None) -> bool:
        """动态调整从站数据块大小。
        
        Args:
            slave_id: 从站ID
            coils: 新的线圈数量（None表示不改变）
            discrete_inputs: 新的离散输入数量（None表示不改变）
            holding_registers: 新的保持寄存器数量（None表示不改变）
            input_registers: 新的输入寄存器数量（None表示不改变）
            
        Returns:
            是否成功
        """
        slave = self.slaves.get(slave_id)
        if not slave:
            return False
        
        # 调整线圈大小
        if coils is not None and coils != len(slave.coils):
            old_coils = slave.coils[:]
            new_coils = [False] * coils
            # 保留原有数据
            copy_len = min(len(old_coils), coils)
            new_coils[:copy_len] = old_coils[:copy_len]
            slave.coils = new_coils
            logger.info(f"从站 {slave_id}: 线圈大小从 {len(old_coils)} 调整到 {coils}")
        
        # 调整离散输入大小
        if discrete_inputs is not None and discrete_inputs != len(slave.discrete_inputs):
            old_inputs = slave.discrete_inputs[:]
            new_inputs = [False] * discrete_inputs
            copy_len = min(len(old_inputs), discrete_inputs)
            new_inputs[:copy_len] = old_inputs[:copy_len]
            slave.discrete_inputs = new_inputs
            logger.info(f"从站 {slave_id}: 离散输入大小从 {len(old_inputs)} 调整到 {discrete_inputs}")
        
        # 调整保持寄存器大小
        if holding_registers is not None and holding_registers != len(slave.holding_registers):
            old_regs = slave.holding_registers[:]
            new_regs = [0] * holding_registers
            copy_len = min(len(old_regs), holding_registers)
            new_regs[:copy_len] = old_regs[:copy_len]
            slave.holding_registers = new_regs
            logger.info(f"从站 {slave_id}: 保持寄存器大小从 {len(old_regs)} 调整到 {holding_registers}")
        
        # 调整输入寄存器大小
        if input_registers is not None and input_registers != len(slave.input_registers):
            old_regs = slave.input_registers[:]
            new_regs = [0] * input_registers
            copy_len = min(len(old_regs), input_registers)
            new_regs[:copy_len] = old_regs[:copy_len]
            slave.input_registers = new_regs
            logger.info(f"从站 {slave_id}: 输入寄存器大小从 {len(old_regs)} 调整到 {input_registers}")
        
        self._modified = True
        return True

    async def read_coils(self, slave_id: int, address: int, count: int) -> Optional[List[bool]]:
        """读取线圈。

        Args:
            slave_id: 从站ID
            address: 起始地址
            count: 数量

        Returns:
            线圈列表，如果失败返回 None
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave:
                return None
            if address + count > len(slave.coils):
                return None
            return slave.coils[address : address + count]

    async def read_discrete_inputs(
        self, slave_id: int, address: int, count: int
    ) -> Optional[List[bool]]:
        """读取离散输入。

        Args:
            slave_id: 从站ID
            address: 起始地址
            count: 数量

        Returns:
            离散输入列表，如果失败返回 None
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave:
                return None
            if address + count > len(slave.discrete_inputs):
                return None
            return slave.discrete_inputs[address : address + count]

    async def read_holding_registers(
        self, slave_id: int, address: int, count: int
    ) -> Optional[List[int]]:
        """读取保持寄存器。

        Args:
            slave_id: 从站ID
            address: 起始地址
            count: 数量

        Returns:
            寄存器列表，如果失败返回 None
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave:
                return None
            if address + count > len(slave.holding_registers):
                return None
            return slave.holding_registers[address : address + count]

    async def read_input_registers(
        self, slave_id: int, address: int, count: int
    ) -> Optional[List[int]]:
        """读取输入寄存器。

        Args:
            slave_id: 从站ID
            address: 起始地址
            count: 数量

        Returns:
            寄存器列表，如果失败返回 None
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave:
                return None
            if address + count > len(slave.input_registers):
                return None
            return slave.input_registers[address : address + count]

    async def write_coil(
        self, slave_id: int, address: int, value: bool, source: str = "unknown"
    ) -> bool:
        """写入单个线圈。

        Args:
            slave_id: 从站ID
            address: 地址
            value: 值
            source: 来源

        Returns:
            是否成功
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave or address >= len(slave.coils):
                return False
            old_value = slave.coils[address]
            slave.coils[address] = value
            self._modified = True
            self._add_history(slave_id, "coils", address, old_value, value, source)
            return True

    async def write_coils(
        self, slave_id: int, address: int, values: List[bool], source: str = "unknown"
    ) -> bool:
        """写入多个线圈。

        Args:
            slave_id: 从站ID
            address: 起始地址
            values: 值列表
            source: 来源

        Returns:
            是否成功
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave or address + len(values) > len(slave.coils):
                return False
            for i, value in enumerate(values):
                old_value = slave.coils[address + i]
                slave.coils[address + i] = value
                self._add_history(slave_id, "coils", address + i, old_value, value, source)
            self._modified = True
            return True

    async def write_register(
        self, slave_id: int, address: int, value: int, source: str = "unknown"
    ) -> bool:
        """写入单个保持寄存器。

        Args:
            slave_id: 从站ID
            address: 地址
            value: 值
            source: 来源

        Returns:
            是否成功
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave or address >= len(slave.holding_registers):
                return False
            old_value = slave.holding_registers[address]
            slave.holding_registers[address] = value & 0xFFFF
            self._modified = True
            self._add_history(
                slave_id, "holding_registers", address, old_value, value & 0xFFFF, source
            )
            return True

    async def write_registers(
        self, slave_id: int, address: int, values: List[int], source: str = "unknown"
    ) -> bool:
        """写入多个保持寄存器。

        Args:
            slave_id: 从站ID
            address: 起始地址
            values: 值列表
            source: 来源

        Returns:
            是否成功
        """
        async with self._lock:
            slave = self.slaves.get(slave_id)
            if not slave or address + len(values) > len(slave.holding_registers):
                return False
            for i, value in enumerate(values):
                old_value = slave.holding_registers[address + i]
                slave.holding_registers[address + i] = value & 0xFFFF
                self._add_history(
                    slave_id, "holding_registers", address + i, old_value, value & 0xFFFF, source
                )
            self._modified = True
            return True

    def _add_history(
        self, slave_id: int, data_type: str, address: int, old_value: any, new_value: any, source: str
    ) -> None:
        """添加历史记录。"""
        record = HistoryRecord(
            timestamp=datetime.now().isoformat(),
            slave_id=slave_id,
            data_type=data_type,
            address=address,
            old_value=old_value,
            new_value=new_value,
            source=source,
        )
        self.history.append(record)
        if len(self.history) > self.history_max_size:
            self.history.pop(0)

    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取历史记录。

        Args:
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        records = self.history[-limit:]
        return [
            {
                "timestamp": r.timestamp,
                "slave_id": r.slave_id,
                "data_type": r.data_type,
                "address": r.address,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "source": r.source,
            }
            for r in records
        ]

    async def save_to_file(self) -> None:
        """保存数据到文件。"""
        if not self.data_file or not self._modified:
            return

        async with self._lock:
            data = {
                "slaves": {
                    slave_id: {
                        "coils": block.coils,
                        "discrete_inputs": block.discrete_inputs,
                        "holding_registers": block.holding_registers,
                        "input_registers": block.input_registers,
                    }
                    for slave_id, block in self.slaves.items()
                }
            }

            try:
                with open(self.data_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                self._modified = False
                logger.info(f"数据已保存到 {self.data_file}")
            except Exception as e:
                logger.error(f"保存数据失败: {e}")

    async def load_from_file(self) -> None:
        """从文件加载数据。"""
        if not self.data_file or not self.data_file.exists():
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            async with self._lock:
                slaves_data = data.get("slaves", {})
                for slave_id_str, block_data in slaves_data.items():
                    slave_id = int(slave_id_str)
                    if slave_id in self.slaves:
                        self.slaves[slave_id].coils = block_data.get("coils", [])
                        self.slaves[slave_id].discrete_inputs = block_data.get(
                            "discrete_inputs", []
                        )
                        self.slaves[slave_id].holding_registers = block_data.get(
                            "holding_registers", []
                        )
                        self.slaves[slave_id].input_registers = block_data.get(
                            "input_registers", []
                        )

            logger.info(f"已从 {self.data_file} 加载数据")
        except Exception as e:
            logger.error(f"加载数据失败: {e}")

    def get_all_data(self) -> Dict:
        """获取所有数据。

        Returns:
            包含所有从站数据的字典
        """
        return {
            slave_id: {
                "coils": block.coils[:],
                "discrete_inputs": block.discrete_inputs[:],
                "holding_registers": block.holding_registers[:],
                "input_registers": block.input_registers[:],
            }
            for slave_id, block in self.slaves.items()
        }
