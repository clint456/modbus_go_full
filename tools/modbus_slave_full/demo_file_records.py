#!/usr/bin/env python3
"""文件记录功能演示脚本 - 通过 Web API 操作文件记录"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def write_register(slave_id, address, value):
    """写入单个寄存器"""
    response = requests.post(
        f"{BASE_URL}/api/write-register",
        json={"slave_id": slave_id, "address": address, "value": value}
    )
    return response.json()

def read_registers(slave_id, start, count):
    """读取多个寄存器"""
    response = requests.get(f"{BASE_URL}/api/data?slave_id={slave_id}")
    data = response.json()
    registers = data.get('holding_registers', {})
    
    result = []
    for i in range(count):
        addr = start + i
        result.append(registers.get(str(addr), 0))
    return result

def demo_file_record_operations():
    """演示文件记录操作"""
    print("=" * 70)
    print("📁 Modbus 文件记录功能演示")
    print("=" * 70)
    
    slave_id = 1
    
    # 演示 1: 写入文件记录
    print("\n【演示 1】写入文件记录 (FC21)")
    print("-" * 70)
    
    file_number = 0
    record_number = 100
    data_values = [111, 222, 333, 444, 555]
    
    print(f"  文件编号: {file_number}")
    print(f"  记录编号: {record_number}")
    print(f"  数据值: {data_values}")
    print(f"  -> 映射到保持寄存器地址 {record_number}-{record_number + len(data_values) - 1}")
    
    print("\n  正在写入...")
    for i, value in enumerate(data_values):
        addr = record_number + i
        result = write_register(slave_id, addr, value)
        print(f"    ✓ 地址 {addr} = {value}")
        time.sleep(0.1)
    
    print("\n  ✅ 写入完成！")
    
    # 演示 2: 读取文件记录
    print("\n【演示 2】读取文件记录 (FC20)")
    print("-" * 70)
    
    print(f"  文件编号: {file_number}")
    print(f"  记录编号: {record_number}")
    print(f"  记录长度: {len(data_values)}")
    print(f"  -> 从保持寄存器地址 {record_number} 开始读取 {len(data_values)} 个")
    
    print("\n  正在读取...")
    read_values = read_registers(slave_id, record_number, len(data_values))
    
    print(f"  读取的数据: {read_values}")
    
    if read_values == data_values:
        print("\n  ✅ 数据验证成功！读取的数据与写入的数据一致")
    else:
        print("\n  ⚠️  数据不一致")
    
    # 演示 3: 多个文件记录区域
    print("\n【演示 3】操作多个文件记录区域")
    print("-" * 70)
    
    file_records = [
        {"file": 0, "record": 10, "data": [10, 20, 30]},
        {"file": 1, "record": 20, "data": [100, 200, 300, 400]},
        {"file": 2, "record": 50, "data": [1000, 2000]},
    ]
    
    for fr in file_records:
        print(f"\n  文件 {fr['file']} - 记录 {fr['record']}")
        print(f"    数据: {fr['data']}")
        print(f"    -> 保持寄存器地址 {fr['record']}-{fr['record'] + len(fr['data']) - 1}")
        
        for i, value in enumerate(fr['data']):
            write_register(slave_id, fr['record'] + i, value)
        
        print(f"    ✓ 写入完成")
        time.sleep(0.1)
    
    print("\n  验证读取...")
    for fr in file_records:
        values = read_registers(slave_id, fr['record'], len(fr['data']))
        match = "✅" if values == fr['data'] else "❌"
        print(f"    {match} 文件 {fr['file']}: {values}")
    
    # 演示 4: 工作原理说明
    print("\n【工作原理】")
    print("-" * 70)
    print("""
  文件记录是 Modbus 的高级功能，用于组织和管理大量寄存器数据：
  
  1. 📂 文件编号 (File Number)
     - 用于逻辑分组，范围 0-65535
     - 本实现中主要用于组织，不影响实际地址
  
  2. 📍 记录编号 (Record Number)  
     - 直接映射到保持寄存器地址
     - 记录编号 100 = 保持寄存器地址 100
  
  3. 📏 记录长度 (Record Length)
     - 指定读写的寄存器数量
     - 最多 120 个寄存器（Modbus 规范限制）
  
  4. 🔄 操作流程
     - FC20 (读): 文件记录参数 -> 读取保持寄存器 -> 返回数据
     - FC21 (写): 文件记录参数 + 数据 -> 写入保持寄存器 -> 确认
  
  5. 💡 使用场景
     - 配置文件管理
     - 参数组管理  
     - 大批量数据传输
     - 结构化数据存储
""")
    
    print("\n" + "=" * 70)
    print("🎉 演示完成！")
    print("=" * 70)
    print("\n提示：")
    print("  - 访问 Web 界面: http://localhost:8080")
    print("  - 切换到 '📁 文件记录' 标签页")
    print("  - 可以直观地看到文件记录的映射关系和操作过程")
    print()

if __name__ == "__main__":
    try:
        demo_file_record_operations()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("请确保 Modbus 服务器正在运行: poetry run modbus-server")
