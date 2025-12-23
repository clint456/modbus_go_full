#!/bin/bash
# 自动化测试脚本 - 无需手动输入

echo "=== Modbus Go 客户端自动化测试 ==="
echo ""
echo "测试配置:"
echo "  模式: TCP"
echo "  主机: 127.0.0.1"
echo "  端口: 5020"
echo ""

# 使用 echo 管道输入自动化选择
echo -e "1\n\n\n" | ./comprehensive_example.o

echo ""
echo "=== 测试完成 ==="
