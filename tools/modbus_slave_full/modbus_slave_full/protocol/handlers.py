"""Modbus 功能码处理器。

实现所有标准 Modbus 功能码的处理逻辑。
"""

import logging
import struct
from typing import Optional, Tuple

from ..datastore import ModbusDataStore
from .utils import bits_to_bytes, bytes_to_bits, bytes_to_words, words_to_bytes

logger = logging.getLogger(__name__)


# 异常码
ILLEGAL_FUNCTION = 0x01
ILLEGAL_DATA_ADDRESS = 0x02
ILLEGAL_DATA_VALUE = 0x03
SLAVE_DEVICE_FAILURE = 0x04


class ModbusHandler:
    """Modbus 功能码处理器。"""

    def __init__(self, datastore: ModbusDataStore):
        """初始化处理器。

        Args:
            datastore: 数据存储
        """
        self.datastore = datastore
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "function_codes": {},
        }

    async def handle_request(
        self, slave_id: int, function_code: int, data: bytes, source: str = "unknown"
    ) -> Optional[bytes]:
        """处理 Modbus 请求。

        Args:
            slave_id: 从站ID
            function_code: 功能码
            data: 请求数据
            source: 请求来源

        Returns:
            响应数据，如果失败返回 None
        """
        self.stats["total_requests"] += 1
        fc_name = f"FC{function_code:02d}"
        self.stats["function_codes"][fc_name] = self.stats["function_codes"].get(fc_name, 0) + 1

        handlers = {
            0x01: self._handle_read_coils,
            0x02: self._handle_read_discrete_inputs,
            0x03: self._handle_read_holding_registers,
            0x04: self._handle_read_input_registers,
            0x05: self._handle_write_single_coil,
            0x06: self._handle_write_single_register,
            0x07: self._handle_read_exception_status,
            0x08: self._handle_diagnostics,
            0x0B: self._handle_get_comm_event_counter,
            0x0C: self._handle_get_comm_event_log,
            0x0F: self._handle_write_multiple_coils,
            0x10: self._handle_write_multiple_registers,
            0x11: self._handle_report_slave_id,
            0x14: self._handle_read_file_record,
            0x15: self._handle_write_file_record,
            0x16: self._handle_mask_write_register,
            0x17: self._handle_read_write_multiple_registers,
            0x18: self._handle_read_fifo_queue,
        }

        handler = handlers.get(function_code)
        if not handler:
            logger.warning(f"不支持的功能码: {function_code}")
            return self._build_exception_response(function_code, ILLEGAL_FUNCTION)

        try:
            response = await handler(slave_id, data, source)
            if response:
                self.stats["successful_requests"] += 1
            return response
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return self._build_exception_response(function_code, SLAVE_DEVICE_FAILURE)

    async def _handle_read_coils(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读线圈请求 (FC01)。"""
        if len(data) < 4:
            return self._build_exception_response(0x01, ILLEGAL_DATA_VALUE)

        address, count = struct.unpack(">HH", data[:4])

        if count < 1 or count > 2000:
            return self._build_exception_response(0x01, ILLEGAL_DATA_VALUE)

        values = await self.datastore.read_coils(slave_id, address, count)
        if values is None:
            return self._build_exception_response(0x01, ILLEGAL_DATA_ADDRESS)

        response_data = bits_to_bytes(values)
        byte_count = len(response_data)
        return struct.pack("BB", 0x01, byte_count) + response_data

    async def _handle_read_discrete_inputs(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读离散输入请求 (FC02)。"""
        if len(data) < 4:
            return self._build_exception_response(0x02, ILLEGAL_DATA_VALUE)

        address, count = struct.unpack(">HH", data[:4])

        if count < 1 or count > 2000:
            return self._build_exception_response(0x02, ILLEGAL_DATA_VALUE)

        values = await self.datastore.read_discrete_inputs(slave_id, address, count)
        if values is None:
            return self._build_exception_response(0x02, ILLEGAL_DATA_ADDRESS)

        response_data = bits_to_bytes(values)
        byte_count = len(response_data)
        return struct.pack("BB", 0x02, byte_count) + response_data

    async def _handle_read_holding_registers(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读保持寄存器请求 (FC03)。"""
        if len(data) < 4:
            return self._build_exception_response(0x03, ILLEGAL_DATA_VALUE)

        address, count = struct.unpack(">HH", data[:4])

        if count < 1 or count > 125:
            return self._build_exception_response(0x03, ILLEGAL_DATA_VALUE)

        values = await self.datastore.read_holding_registers(slave_id, address, count)
        if values is None:
            return self._build_exception_response(0x03, ILLEGAL_DATA_ADDRESS)

        response_data = words_to_bytes(values)
        byte_count = len(response_data)
        return struct.pack("BB", 0x03, byte_count) + response_data

    async def _handle_read_input_registers(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读输入寄存器请求 (FC04)。"""
        if len(data) < 4:
            return self._build_exception_response(0x04, ILLEGAL_DATA_VALUE)

        address, count = struct.unpack(">HH", data[:4])

        if count < 1 or count > 125:
            return self._build_exception_response(0x04, ILLEGAL_DATA_VALUE)

        values = await self.datastore.read_input_registers(slave_id, address, count)
        if values is None:
            return self._build_exception_response(0x04, ILLEGAL_DATA_ADDRESS)

        response_data = words_to_bytes(values)
        byte_count = len(response_data)
        return struct.pack("BB", 0x04, byte_count) + response_data

    async def _handle_write_single_coil(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理写单个线圈请求 (FC05)。"""
        if len(data) < 4:
            return self._build_exception_response(0x05, ILLEGAL_DATA_VALUE)

        address, value = struct.unpack(">HH", data[:4])

        if value not in (0x0000, 0xFF00):
            return self._build_exception_response(0x05, ILLEGAL_DATA_VALUE)

        coil_value = value == 0xFF00
        success = await self.datastore.write_coil(slave_id, address, coil_value, source)

        if not success:
            return self._build_exception_response(0x05, ILLEGAL_DATA_ADDRESS)

        return struct.pack(">BHH", 0x05, address, value)

    async def _handle_write_single_register(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理写单个寄存器请求 (FC06)。"""
        if len(data) < 4:
            return self._build_exception_response(0x06, ILLEGAL_DATA_VALUE)

        address, value = struct.unpack(">HH", data[:4])

        success = await self.datastore.write_register(slave_id, address, value, source)

        if not success:
            return self._build_exception_response(0x06, ILLEGAL_DATA_ADDRESS)

        return struct.pack(">BHH", 0x06, address, value)

    async def _handle_write_multiple_coils(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理写多个线圈请求 (FC15)。"""
        if len(data) < 5:
            return self._build_exception_response(0x0F, ILLEGAL_DATA_VALUE)

        address, count, byte_count = struct.unpack(">HHB", data[:5])

        if count < 1 or count > 1968 or byte_count != (count + 7) // 8:
            return self._build_exception_response(0x0F, ILLEGAL_DATA_VALUE)

        if len(data) < 5 + byte_count:
            return self._build_exception_response(0x0F, ILLEGAL_DATA_VALUE)

        coil_data = data[5 : 5 + byte_count]
        values = bytes_to_bits(coil_data, count)

        success = await self.datastore.write_coils(slave_id, address, values, source)

        if not success:
            return self._build_exception_response(0x0F, ILLEGAL_DATA_ADDRESS)

        return struct.pack(">BHH", 0x0F, address, count)

    async def _handle_write_multiple_registers(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理写多个寄存器请求 (FC16)。"""
        if len(data) < 5:
            return self._build_exception_response(0x10, ILLEGAL_DATA_VALUE)

        address, count, byte_count = struct.unpack(">HHB", data[:5])

        if count < 1 or count > 123 or byte_count != count * 2:
            return self._build_exception_response(0x10, ILLEGAL_DATA_VALUE)

        if len(data) < 5 + byte_count:
            return self._build_exception_response(0x10, ILLEGAL_DATA_VALUE)

        register_data = data[5 : 5 + byte_count]
        values = bytes_to_words(register_data)

        success = await self.datastore.write_registers(slave_id, address, values, source)

        if not success:
            return self._build_exception_response(0x10, ILLEGAL_DATA_ADDRESS)

        return struct.pack(">BHH", 0x10, address, count)

    async def _handle_read_write_multiple_registers(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读写多个寄存器请求 (FC23)。"""
        if len(data) < 9:
            return self._build_exception_response(0x17, ILLEGAL_DATA_VALUE)

        read_address, read_count, write_address, write_count, byte_count = struct.unpack(
            ">HHHHB", data[:9]
        )

        if read_count < 1 or read_count > 125 or write_count < 1 or write_count > 121:
            return self._build_exception_response(0x17, ILLEGAL_DATA_VALUE)

        if byte_count != write_count * 2 or len(data) < 9 + byte_count:
            return self._build_exception_response(0x17, ILLEGAL_DATA_VALUE)

        # 先写
        register_data = data[9 : 9 + byte_count]
        values = bytes_to_words(register_data)
        write_success = await self.datastore.write_registers(
            slave_id, write_address, values, source
        )

        if not write_success:
            return self._build_exception_response(0x17, ILLEGAL_DATA_ADDRESS)

        # 再读
        read_values = await self.datastore.read_holding_registers(
            slave_id, read_address, read_count
        )
        if read_values is None:
            return self._build_exception_response(0x17, ILLEGAL_DATA_ADDRESS)

        response_data = words_to_bytes(read_values)
        response_byte_count = len(response_data)
        return struct.pack("BB", 0x17, response_byte_count) + response_data

    async def _handle_read_exception_status(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读异常状态请求 (FC07)。
        
        返回8位异常状态，每位代表一个特定的异常。
        """
        # 简单实现：返回无异常状态
        exception_status = 0x00
        return struct.pack("BB", 0x07, exception_status)

    async def _handle_diagnostics(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理诊断请求 (FC08)。
        
        支持多种诊断子功能。
        """
        if len(data) < 4:
            return self._build_exception_response(0x08, ILLEGAL_DATA_VALUE)

        sub_function, diag_data = struct.unpack(">HH", data[:4])

        # 简单实现：回显请求数据
        return struct.pack(">BHH", 0x08, sub_function, diag_data)

    async def _handle_get_comm_event_counter(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理获取通信事件计数器请求 (FC11)。
        
        返回状态字和事件计数。
        """
        status = 0xFFFF  # 表示设备就绪
        event_count = self.stats["total_requests"] & 0xFFFF
        return struct.pack(">BHH", 0x0B, status, event_count)

    async def _handle_get_comm_event_log(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理获取通信事件日志请求 (FC12)。
        
        返回事件计数、消息计数和事件日志。
        """
        status = 0xFFFF
        event_count = self.stats["total_requests"] & 0xFFFF
        message_count = self.stats["successful_requests"] & 0xFFFF
        
        # 简化实现：返回空事件日志
        byte_count = 6
        events = b""
        
        response = struct.pack(">BBHHH", 0x0C, byte_count, status, event_count, message_count)
        return response + events

    async def _handle_report_slave_id(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理报告从站ID请求 (FC17)。
        
        返回从站ID、运行状态和其他从站特定数据。
        """
        # 从站ID信息
        slave_id_info = f"Modbus Slave {slave_id}".encode("ascii")
        run_indicator = 0xFF  # 0xFF = ON, 0x00 = OFF
        
        byte_count = len(slave_id_info) + 1
        return struct.pack("BB", 0x11, byte_count) + slave_id_info + bytes([run_indicator])

    async def _handle_read_file_record(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读文件记录请求 (FC20)。
        
        支持从多个文件中读取记录。
        """
        if len(data) < 8:  # 最少需要 byte_count + 1个子请求(7字节)
            return self._build_exception_response(0x14, ILLEGAL_DATA_VALUE)

        byte_count = data[0]
        if len(data) < 1 + byte_count or byte_count < 7:
            return self._build_exception_response(0x14, ILLEGAL_DATA_VALUE)

        # 解析子请求
        response_data = bytearray()
        offset = 1

        while offset + 7 <= 1 + byte_count:
            ref_type = data[offset]
            file_number, record_number, record_length = struct.unpack(
                ">HHH", data[offset + 1 : offset + 7]
            )

            if ref_type != 0x06:
                return self._build_exception_response(0x14, ILLEGAL_DATA_VALUE)

            # 限制记录长度以避免字节溢出
            if record_length > 120:
                return self._build_exception_response(0x14, ILLEGAL_DATA_VALUE)

            # 从保持寄存器读取（将文件映射到寄存器）
            file_offset = file_number * 10000
            start_address = file_offset + record_number
            
            values = await self.datastore.read_holding_registers(
                slave_id, start_address, record_length
            )

            if values is None:
                return self._build_exception_response(0x14, ILLEGAL_DATA_ADDRESS)

            # 构建子响应
            sub_response_length = record_length * 2 + 1  # 数据字节数 + ref_type
            response_data.append(sub_response_length & 0xFF)
            response_data.append(ref_type)
            response_data.extend(words_to_bytes(values))

            offset += 7

        total_length = len(response_data)
        if total_length > 255:
            return self._build_exception_response(0x14, ILLEGAL_DATA_VALUE)
            
        return struct.pack("BB", 0x14, total_length) + bytes(response_data)

    async def _handle_write_file_record(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理写文件记录请求 (FC21)。
        
        支持向多个文件写入记录。
        """
        if len(data) < 8:  # 最少需要 byte_count + 1个子请求(7字节) + 数据
            return self._build_exception_response(0x15, ILLEGAL_DATA_VALUE)

        byte_count = data[0]
        if len(data) < 1 + byte_count:
            return self._build_exception_response(0x15, ILLEGAL_DATA_VALUE)

        # 解析并处理子请求
        offset = 1

        while offset + 7 <= 1 + byte_count:
            ref_type = data[offset]
            file_number, record_number, record_length = struct.unpack(
                ">HHH", data[offset + 1 : offset + 7]
            )

            if ref_type != 0x06:
                return self._build_exception_response(0x15, ILLEGAL_DATA_VALUE)

            # 限制记录长度
            if record_length > 120:
                return self._build_exception_response(0x15, ILLEGAL_DATA_VALUE)

            data_length = record_length * 2
            if offset + 7 + data_length > len(data):
                return self._build_exception_response(0x15, ILLEGAL_DATA_VALUE)

            # 提取寄存器值
            register_data = data[offset + 7 : offset + 7 + data_length]
            values = bytes_to_words(register_data)

            # 写入保持寄存器（将文件映射到寄存器）
            file_offset = file_number * 10000
            start_address = file_offset + record_number

            success = await self.datastore.write_registers(
                slave_id, start_address, values, source
            )

            if not success:
                return self._build_exception_response(0x15, ILLEGAL_DATA_ADDRESS)

            offset += 7 + data_length

        # 回显请求
        return bytes([0x15]) + data[:byte_count + 1]

    async def _handle_mask_write_register(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理屏蔽写寄存器请求 (FC22)。
        
        使用AND和OR屏蔽修改寄存器值。
        """
        if len(data) < 6:
            return self._build_exception_response(0x16, ILLEGAL_DATA_VALUE)

        address, and_mask, or_mask = struct.unpack(">HHH", data[:6])

        # 读取当前值
        current_values = await self.datastore.read_holding_registers(slave_id, address, 1)
        if current_values is None:
            return self._build_exception_response(0x16, ILLEGAL_DATA_ADDRESS)

        # 应用屏蔽: Result = (Current AND And_Mask) OR (Or_Mask AND (NOT And_Mask))
        current_value = current_values[0]
        new_value = (current_value & and_mask) | (or_mask & (~and_mask & 0xFFFF))

        # 写入新值
        success = await self.datastore.write_register(slave_id, address, new_value, source)
        if not success:
            return self._build_exception_response(0x16, ILLEGAL_DATA_ADDRESS)

        # 回显请求
        return struct.pack(">BHHH", 0x16, address, and_mask, or_mask)

    async def _handle_read_fifo_queue(
        self, slave_id: int, data: bytes, source: str
    ) -> Optional[bytes]:
        """处理读FIFO队列请求 (FC24)。
        
        从FIFO队列中读取数据。
        """
        if len(data) < 2:
            return self._build_exception_response(0x18, ILLEGAL_DATA_VALUE)

        fifo_address = struct.unpack(">H", data[:2])[0]

        # 简化实现：从保持寄存器读取
        # 第一个寄存器存储FIFO计数，后续寄存器存储FIFO数据
        count_register = await self.datastore.read_holding_registers(slave_id, fifo_address, 1)
        if count_register is None:
            return self._build_exception_response(0x18, ILLEGAL_DATA_ADDRESS)

        fifo_count = min(count_register[0], 31)  # 最多31个值

        if fifo_count > 0:
            fifo_values = await self.datastore.read_holding_registers(
                slave_id, fifo_address + 1, fifo_count
            )
            if fifo_values is None:
                return self._build_exception_response(0x18, ILLEGAL_DATA_ADDRESS)
        else:
            fifo_values = []

        # 构建响应
        byte_count = (fifo_count + 1) * 2
        response = struct.pack(">BHH", 0x18, byte_count, fifo_count)
        if fifo_values:
            response += words_to_bytes(fifo_values)

        return response

    def _build_exception_response(self, function_code: int, exception_code: int) -> bytes:
        """构建异常响应。"""
        return struct.pack("BB", function_code | 0x80, exception_code)

    def get_stats(self) -> dict:
        """获取统计信息。"""
        return self.stats.copy()
