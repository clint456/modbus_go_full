#!/usr/bin/env python3
"""Modbus 客户端测试脚本 - 测试所有功能码 FC01-24。"""

import asyncio
import struct
from typing import List, Tuple


class ModbusTCPClient:
    """简单的 Modbus TCP 客户端。"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5020):
        self.host = host
        self.port = port
        self.transaction_id = 0
        self.reader = None
        self.writer = None
    
    async def connect(self):
        """连接到 Modbus 服务器。"""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"✓ 已连接到 {self.host}:{self.port}")
    
    async def close(self):
        """关闭连接。"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("✓ 连接已关闭")
    
    async def send_request(self, slave_id: int, function_code: int, data: bytes) -> bytes:
        """发送 Modbus 请求并接收响应。"""
        self.transaction_id += 1
        
        # 构建 MBAP 头
        mbap = struct.pack(">HHHB", 
            self.transaction_id,  # 事务ID
            0,                    # 协议ID (Modbus = 0)
            len(data) + 2,       # 长度 (slave_id + function_code + data)
            slave_id             # 从站ID
        )
        
        # 完整请求
        request = mbap + bytes([function_code]) + data
        
        # 发送请求
        self.writer.write(request)
        await self.writer.drain()
        
        # 接收响应头
        header = await self.reader.readexactly(7)
        trans_id, proto_id, length, resp_slave_id = struct.unpack(">HHHB", header)
        
        # 接收响应数据
        response_data = await self.reader.readexactly(length - 1)
        
        return response_data
    
    # ============================================================
    # 功能码实现
    # ============================================================
    
    async def read_coils(self, slave_id: int, address: int, count: int) -> List[bool]:
        """FC01: 读线圈。"""
        data = struct.pack(">HH", address, count)
        response = await self.send_request(slave_id, 0x01, data)
        
        fc = response[0]
        if fc == 0x81:  # 异常响应
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        coil_bytes = response[2:2+byte_count]
        
        coils = []
        for byte in coil_bytes:
            for i in range(8):
                if len(coils) < count:
                    coils.append(bool(byte & (1 << i)))
        
        return coils[:count]
    
    async def read_discrete_inputs(self, slave_id: int, address: int, count: int) -> List[bool]:
        """FC02: 读离散输入。"""
        data = struct.pack(">HH", address, count)
        response = await self.send_request(slave_id, 0x02, data)
        
        fc = response[0]
        if fc == 0x82:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        input_bytes = response[2:2+byte_count]
        
        inputs = []
        for byte in input_bytes:
            for i in range(8):
                if len(inputs) < count:
                    inputs.append(bool(byte & (1 << i)))
        
        return inputs[:count]
    
    async def read_holding_registers(self, slave_id: int, address: int, count: int) -> List[int]:
        """FC03: 读保持寄存器。"""
        data = struct.pack(">HH", address, count)
        response = await self.send_request(slave_id, 0x03, data)
        
        fc = response[0]
        if fc == 0x83:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        values = struct.unpack(f">{count}H", response[2:2+byte_count])
        return list(values)
    
    async def read_input_registers(self, slave_id: int, address: int, count: int) -> List[int]:
        """FC04: 读输入寄存器。"""
        data = struct.pack(">HH", address, count)
        response = await self.send_request(slave_id, 0x04, data)
        
        fc = response[0]
        if fc == 0x84:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        values = struct.unpack(f">{count}H", response[2:2+byte_count])
        return list(values)
    
    async def write_single_coil(self, slave_id: int, address: int, value: bool) -> bool:
        """FC05: 写单个线圈。"""
        coil_value = 0xFF00 if value else 0x0000
        data = struct.pack(">HH", address, coil_value)
        response = await self.send_request(slave_id, 0x05, data)
        
        fc = response[0]
        if fc == 0x85:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def write_single_register(self, slave_id: int, address: int, value: int) -> bool:
        """FC06: 写单个寄存器。"""
        data = struct.pack(">HH", address, value)
        response = await self.send_request(slave_id, 0x06, data)
        
        fc = response[0]
        if fc == 0x86:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def read_exception_status(self, slave_id: int) -> int:
        """FC07: 读异常状态。"""
        response = await self.send_request(slave_id, 0x07, b"")
        
        fc = response[0]
        if fc == 0x87:
            raise Exception(f"异常代码: {response[1]}")
        
        return response[1]
    
    async def diagnostics(self, slave_id: int, sub_function: int, data: int) -> Tuple[int, int]:
        """FC08: 诊断。"""
        request_data = struct.pack(">HH", sub_function, data)
        response = await self.send_request(slave_id, 0x08, request_data)
        
        fc = response[0]
        if fc == 0x88:
            raise Exception(f"异常代码: {response[1]}")
        
        sub_func, response_data = struct.unpack(">HH", response[1:5])
        return sub_func, response_data
    
    async def get_comm_event_counter(self, slave_id: int) -> Tuple[int, int]:
        """FC11 (0x0B): 获取通信事件计数器。"""
        response = await self.send_request(slave_id, 0x0B, b"")
        
        fc = response[0]
        if fc == 0x8B:
            raise Exception(f"异常代码: {response[1]}")
        
        status, event_count = struct.unpack(">HH", response[1:5])
        return status, event_count
    
    async def get_comm_event_log(self, slave_id: int) -> dict:
        """FC12 (0x0C): 获取通信事件日志。"""
        response = await self.send_request(slave_id, 0x0C, b"")
        
        fc = response[0]
        if fc == 0x8C:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        status, event_count, message_count = struct.unpack(">HHH", response[2:8])
        
        return {
            "status": status,
            "event_count": event_count,
            "message_count": message_count
        }
    
    async def write_multiple_coils(self, slave_id: int, address: int, values: List[bool]) -> bool:
        """FC15 (0x0F): 写多个线圈。"""
        count = len(values)
        byte_count = (count + 7) // 8
        
        # 转换布尔值为字节
        coil_bytes = []
        for i in range(byte_count):
            byte_val = 0
            for j in range(8):
                idx = i * 8 + j
                if idx < count and values[idx]:
                    byte_val |= (1 << j)
            coil_bytes.append(byte_val)
        
        data = struct.pack(">HHB", address, count, byte_count) + bytes(coil_bytes)
        response = await self.send_request(slave_id, 0x0F, data)
        
        fc = response[0]
        if fc == 0x8F:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def write_multiple_registers(self, slave_id: int, address: int, values: List[int]) -> bool:
        """FC16 (0x10): 写多个寄存器。"""
        count = len(values)
        byte_count = count * 2
        
        data = struct.pack(">HHB", address, count, byte_count)
        for value in values:
            data += struct.pack(">H", value)
        
        response = await self.send_request(slave_id, 0x10, data)
        
        fc = response[0]
        if fc == 0x90:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def report_slave_id(self, slave_id: int) -> dict:
        """FC17 (0x11): 报告从站ID。"""
        response = await self.send_request(slave_id, 0x11, b"")
        
        fc = response[0]
        if fc == 0x91:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        slave_id_resp = response[2]
        run_indicator = response[3] == 0xFF
        
        return {
            "slave_id": slave_id_resp,
            "run_indicator": run_indicator,
            "byte_count": byte_count
        }
    
    async def read_write_multiple_registers(self, slave_id: int, read_address: int, read_count: int,
                                           write_address: int, write_values: List[int]) -> List[int]:
        """FC23 (0x17): 读写多个寄存器。"""
        write_count = len(write_values)
        write_byte_count = write_count * 2
        
        data = struct.pack(">HHHHB", read_address, read_count, write_address, write_count, write_byte_count)
        for value in write_values:
            data += struct.pack(">H", value)
        
        response = await self.send_request(slave_id, 0x17, data)
        
        fc = response[0]
        if fc == 0x97:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = response[1]
        values = struct.unpack(f">{read_count}H", response[2:2+byte_count])
        return list(values)
    
    async def read_file_record(self, slave_id: int, file_number: int, record_number: int, 
                              record_length: int) -> List[int]:
        """FC20 (0x14): 读文件记录。"""
        # 构建子请求: byte_count + ref_type + file_number + record_number + record_length
        byte_count = 7
        data = bytes([byte_count]) + struct.pack(">BHHH", 0x06, file_number, record_number, record_length)
        
        response = await self.send_request(slave_id, 0x14, data)
        
        fc = response[0]
        if fc == 0x94:
            raise Exception(f"异常代码: {response[1]}")
        
        resp_byte_count = response[1]
        sub_resp_len = response[2]
        ref_type = response[3]
        
        # 解析寄存器值
        data_bytes = response[4:4 + sub_resp_len - 1]
        values = struct.unpack(f">{len(data_bytes)//2}H", data_bytes)
        return list(values)
    
    async def write_file_record(self, slave_id: int, file_number: int, record_number: int, 
                               values: List[int]) -> bool:
        """FC21 (0x15): 写文件记录。"""
        record_length = len(values)
        byte_count = 7 + record_length * 2
        
        data = bytes([byte_count]) + struct.pack(">BHHH", 0x06, file_number, record_number, record_length)
        for value in values:
            data += struct.pack(">H", value)
        
        response = await self.send_request(slave_id, 0x15, data)
        
        fc = response[0]
        if fc == 0x95:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def mask_write_register(self, slave_id: int, address: int, and_mask: int, or_mask: int) -> bool:
        """FC22 (0x16): 屏蔽写寄存器。"""
        data = struct.pack(">HHH", address, and_mask, or_mask)
        response = await self.send_request(slave_id, 0x16, data)
        
        fc = response[0]
        if fc == 0x96:
            raise Exception(f"异常代码: {response[1]}")
        
        return True
    
    async def read_fifo_queue(self, slave_id: int, fifo_address: int) -> List[int]:
        """FC24 (0x18): 读FIFO队列。"""
        data = struct.pack(">H", fifo_address)
        response = await self.send_request(slave_id, 0x18, data)
        
        fc = response[0]
        if fc == 0x98:
            raise Exception(f"异常代码: {response[1]}")
        
        byte_count = struct.unpack(">H", response[1:3])[0]
        fifo_count = struct.unpack(">H", response[3:5])[0]
        
        values = []
        for i in range(fifo_count):
            value = struct.unpack(">H", response[5+i*2:7+i*2])[0]
            values.append(value)
        
        return values


async def test_all_functions():
    """测试所有功能码。"""
    client = ModbusTCPClient()
    
    try:
        await client.connect()
        
        print("\n" + "="*70)
        print("开始测试所有 Modbus 功能码 (FC01-24)")
        print("="*70)
        
        slave_id = 1
        
        # ========== FC01: 读线圈 ==========
        print("\n【FC01】读线圈")
        await client.write_single_coil(slave_id, 0, True)
        await client.write_single_coil(slave_id, 1, False)
        await client.write_single_coil(slave_id, 2, True)
        coils = await client.read_coils(slave_id, 0, 3)
        print(f"  地址 0-2 的线圈值: {coils}")
        
        # ========== FC02: 读离散输入 ==========
        print("\n【FC02】读离散输入")
        inputs = await client.read_discrete_inputs(slave_id, 0, 5)
        print(f"  地址 0-4 的离散输入: {inputs}")
        
        # ========== FC03: 读保持寄存器 ==========
        print("\n【FC03】读保持寄存器")
        await client.write_single_register(slave_id, 10, 1234)
        await client.write_single_register(slave_id, 11, 5678)
        registers = await client.read_holding_registers(slave_id, 10, 2)
        print(f"  地址 10-11 的寄存器值: {registers}")
        
        # ========== FC04: 读输入寄存器 ==========
        print("\n【FC04】读输入寄存器")
        input_regs = await client.read_input_registers(slave_id, 0, 3)
        print(f"  地址 0-2 的输入寄存器: {input_regs}")
        
        # ========== FC05: 写单个线圈 ==========
        print("\n【FC05】写单个线圈")
        await client.write_single_coil(slave_id, 10, True)
        result = await client.read_coils(slave_id, 10, 1)
        print(f"  写入地址 10, 值 True, 读回: {result[0]}")
        
        # ========== FC06: 写单个寄存器 ==========
        print("\n【FC06】写单个寄存器")
        await client.write_single_register(slave_id, 20, 9999)
        result = await client.read_holding_registers(slave_id, 20, 1)
        print(f"  写入地址 20, 值 9999, 读回: {result[0]}")
        
        # ========== FC07: 读异常状态 ==========
        print("\n【FC07】读异常状态")
        status = await client.read_exception_status(slave_id)
        print(f"  异常状态字节: 0x{status:02X}")
        
        # ========== FC08: 诊断 ==========
        print("\n【FC08】诊断 (返回查询数据)")
        sub_func, data = await client.diagnostics(slave_id, 0x0000, 0x1234)
        print(f"  子功能: 0x{sub_func:04X}, 返回数据: 0x{data:04X}")
        
        # ========== FC11 (0x0B): 获取通信事件计数器 ==========
        print("\n【FC11】获取通信事件计数器")
        status, count = await client.get_comm_event_counter(slave_id)
        print(f"  状态: 0x{status:04X}, 事件计数: {count}")
        
        # ========== FC12 (0x0C): 获取通信事件日志 ==========
        print("\n【FC12】获取通信事件日志")
        log = await client.get_comm_event_log(slave_id)
        print(f"  状态: 0x{log['status']:04X}")
        print(f"  事件计数: {log['event_count']}")
        print(f"  消息计数: {log['message_count']}")
        
        # ========== FC15 (0x0F): 写多个线圈 ==========
        print("\n【FC15】写多个线圈")
        coil_values = [True, False, True, True, False]
        await client.write_multiple_coils(slave_id, 20, coil_values)
        result = await client.read_coils(slave_id, 20, 5)
        print(f"  写入地址 20-24: {coil_values}")
        print(f"  读回值: {result}")
        
        # ========== FC16 (0x10): 写多个寄存器 ==========
        print("\n【FC16】写多个寄存器")
        reg_values = [111, 222, 333, 444]
        await client.write_multiple_registers(slave_id, 30, reg_values)
        result = await client.read_holding_registers(slave_id, 30, 4)
        print(f"  写入地址 30-33: {reg_values}")
        print(f"  读回值: {result}")
        
        # ========== FC17 (0x11): 报告从站ID ==========
        print("\n【FC17】报告从站ID")
        slave_info = await client.report_slave_id(slave_id)
        print(f"  从站ID: {slave_info['slave_id']}")
        print(f"  运行状态: {'运行' if slave_info['run_indicator'] else '停止'}")
        
        # ========== FC20 (0x14): 读文件记录 ==========
        print("\n【FC20】读文件记录")
        # 先写入一些数据
        await client.write_multiple_registers(slave_id, 50, [10, 20, 30, 40, 50])
        # 读取文件记录
        file_data = await client.read_file_record(slave_id, 0, 50, 5)
        print(f"  文件 0, 记录 50, 长度 5: {file_data}")
        
        # ========== FC21 (0x15): 写文件记录 ==========
        print("\n【FC21】写文件记录")
        file_values = [100, 200, 300]
        await client.write_file_record(slave_id, 0, 60, file_values)
        # 验证写入
        result = await client.read_holding_registers(slave_id, 60, 3)
        print(f"  写入文件 0, 记录 60: {file_values}")
        print(f"  读回值: {result}")
        
        # ========== FC22 (0x16): 屏蔽写寄存器 ==========
        print("\n【FC22】屏蔽写寄存器")
        # 先设置初始值
        await client.write_single_register(slave_id, 40, 0x0012)
        # 执行屏蔽写操作: Result = (Current AND And_Mask) OR (Or_Mask AND (NOT And_Mask))
        await client.mask_write_register(slave_id, 40, 0x00F2, 0x0025)
        result = await client.read_holding_registers(slave_id, 40, 1)
        expected = (0x0012 & 0x00F2) | (0x0025 & (~0x00F2 & 0xFFFF))
        print(f"  地址 40, 原值: 0x0012")
        print(f"  AND掩码: 0x00F2, OR掩码: 0x0025")
        print(f"  结果: 0x{result[0]:04X} (期望: 0x{expected:04X})")
        
        # ========== FC23 (0x17): 读写多个寄存器 ==========
        print("\n【FC23】读写多个寄存器")
        # 先设置要读的寄存器
        await client.write_multiple_registers(slave_id, 70, [70, 80, 90])
        # 同时读和写
        write_values = [111, 222]
        read_result = await client.read_write_multiple_registers(
            slave_id, 70, 3, 75, write_values
        )
        print(f"  读取地址 70-72: {read_result}")
        print(f"  同时写入地址 75-76: {write_values}")
        # 验证写入
        verify = await client.read_holding_registers(slave_id, 75, 2)
        print(f"  验证写入: {verify}")
        
        # ========== FC24 (0x18): 读FIFO队列 ==========
        print("\n【FC24】读FIFO队列")
        # 设置FIFO: 地址80存储计数，81-85存储数据
        await client.write_single_register(slave_id, 80, 5)
        await client.write_multiple_registers(slave_id, 81, [11, 22, 33, 44, 55])
        fifo_data = await client.read_fifo_queue(slave_id, 80)
        print(f"  FIFO地址 80, 数据: {fifo_data}")
        
        print("\n" + "="*70)
        print("✓ 所有功能码测试完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    print("Modbus TCP 全功能码测试客户端")
    print("支持功能码: FC01-24")
    print("-" * 70)
    asyncio.run(test_all_functions())
