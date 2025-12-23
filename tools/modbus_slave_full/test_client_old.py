#!/usr/bin/env python3
"""Modbus 客户端测试脚本。

用于测试 Modbus 服务器的功能。需要安装 pymodbus:
    pip install pymodbus
"""

import sys

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    print("错误: 需要安装 pymodbus")
    print("运行: pip install pymodbus")
    sys.exit(1)


def test_modbus_server():
    """测试 Modbus 服务器。"""
    # 连接到服务器
    client = ModbusTcpClient("localhost", port=5020)

    if not client.connect():
        print("❌ 无法连接到 Modbus 服务器")
        print("请确保服务器正在运行: poetry run modbus-server")
        return False

    print("✅ 成功连接到 Modbus 服务器")

    try:
        # 测试读取线圈
        print("\n📖 测试读取线圈 (FC01)...")
        result = client.read_coils(0, 10, slave=1)
        if not result.isError():
            print(f"   成功读取 10 个线圈: {result.bits[:10]}")
        else:
            print(f"   ❌ 错误: {result}")

        # 测试读取保持寄存器
        print("\n📖 测试读取保持寄存器 (FC03)...")
        result = client.read_holding_registers(0, 10, slave=1)
        if not result.isError():
            print(f"   成功读取 10 个寄存器: {result.registers}")
        else:
            print(f"   ❌ 错误: {result}")

        # 测试写入单个线圈
        print("\n✍️  测试写入单个线圈 (FC05)...")
        result = client.write_coil(5, True, slave=1)
        if not result.isError():
            print(f"   成功写入线圈 5 = True")
        else:
            print(f"   ❌ 错误: {result}")

        # 测试写入单个寄存器
        print("\n✍️  测试写入单个寄存器 (FC06)...")
        result = client.write_register(5, 1234, slave=1)
        if not result.isError():
            print(f"   成功写入寄存器 5 = 1234")
        else:
            print(f"   ❌ 错误: {result}")

        # 验证写入
        print("\n🔍 验证写入的值...")
        result = client.read_coils(5, 1, slave=1)
        if not result.isError():
            print(f"   线圈 5 = {result.bits[0]} (期望: True)")
        else:
            print(f"   ❌ 错误: {result}")

        result = client.read_holding_registers(5, 1, slave=1)
        if not result.isError():
            print(f"   寄存器 5 = {result.registers[0]} (期望: 1234)")
        else:
            print(f"   ❌ 错误: {result}")

        # 测试写入多个线圈
        print("\n✍️  测试写入多个线圈 (FC15)...")
        result = client.write_coils(10, [True, False, True, False, True], slave=1)
        if not result.isError():
            print(f"   成功写入 5 个线圈")
        else:
            print(f"   ❌ 错误: {result}")

        # 测试写入多个寄存器
        print("\n✍️  测试写入多个寄存器 (FC16)...")
        result = client.write_registers(10, [100, 200, 300, 400, 500], slave=1)
        if not result.isError():
            print(f"   成功写入 5 个寄存器")
        else:
            print(f"   ❌ 错误: {result}")

        print("\n✅ 所有测试完成！")
        print("\n💡 提示:")
        print("   - 访问 http://localhost:8080 查看 Web 控制台")
        print("   - 检查服务器日志查看详细信息")
        print("   - 数据已保存到 modbus_data.json")

        return True

    finally:
        client.close()
        print("\n🔌 已断开连接")


if __name__ == "__main__":
    print("=" * 60)
    print("Modbus 服务器测试脚本")
    print("=" * 60)
    success = test_modbus_server()
    sys.exit(0 if success else 1)
