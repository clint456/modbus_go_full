#!/bin/bash

echo "=============================================================="
echo "🎯 配置管理功能快速验证"
echo "=============================================================="
echo ""

echo "【步骤 1】获取当前配置"
echo "--------------------------------------------------------------"
config=$(curl -s "http://localhost:8080/api/config?slave_id=1")
echo "$config" | python3 -m json.tool
echo ""

echo "【步骤 2】扩大保持寄存器到 2000"
echo "--------------------------------------------------------------"
result=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 2000}')
echo "$result" | python3 -m json.tool
echo ""

echo "【步骤 3】写入长字符串到地址 500（需要大空间）"
echo "--------------------------------------------------------------"
text="配置管理功能测试：现在可以动态调整寄存器大小了！This is a test of dynamic configuration management. We can now resize registers on the fly!"
write_result=$(curl -s -X POST http://localhost:8080/api/write/string \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": 1, \"address\": 500, \"text\": \"$text\"}")
echo "$write_result" | python3 -m json.tool
echo ""

echo "【步骤 4】读取字符串并验证"
echo "--------------------------------------------------------------"
count=$(echo "$write_result" | python3 -c "import json, sys; print(json.load(sys.stdin).get('registers_written', 0))")
read_result=$(curl -s "http://localhost:8080/api/read/string?slave_id=1&address=500&count=$count")
echo "$read_result" | python3 -m json.tool
echo ""

read_text=$(echo "$read_result" | python3 -c "import json, sys; print(json.load(sys.stdin).get('text', ''))")
if [ "$read_text" = "$text" ]; then
    echo "✅ 字符串读写一致！"
else
    echo "❌ 字符串不一致"
    echo "   写入: $text"
    echo "   读取: $read_text"
fi
echo ""

echo "【步骤 5】缩小到 1000 并验证数据保留"
echo "--------------------------------------------------------------"
result=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 1000}')
echo "$result" | python3 -m json.tool
echo ""

# 验证地址 500 附近的数据仍在（在 1000 范围内）
read_result=$(curl -s "http://localhost:8080/api/read/string?slave_id=1&address=500&count=10")
partial_text=$(echo "$read_result" | python3 -c "import json, sys; print(json.load(sys.stdin).get('text', ''))")
echo "地址 500 的部分数据: ${partial_text:0:50}..."
if [ -n "$partial_text" ]; then
    echo "✅ 缩小后数据保留正常！"
else
    echo "❌ 数据丢失"
fi
echo ""

echo "【步骤 6】同时调整多种数据类型"
echo "--------------------------------------------------------------"
result=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "coils": 500, "discrete_inputs": 500, "holding_registers": 5000, "input_registers": 1000}')
echo "$result" | python3 -m json.tool
echo ""

echo "【步骤 7】验证最终配置"
echo "--------------------------------------------------------------"
final_config=$(curl -s "http://localhost:8080/api/config?slave_id=1")
echo "$final_config" | python3 -m json.tool
echo ""

echo "=============================================================="
echo "✅ 配置管理功能验证完成！"
echo ""
echo "💡 现在可以在 Web 界面使用配置管理功能："
echo "   1. 访问 http://localhost:8080"
echo "   2. 切换到 '⚙️ 配置' 标签页"
echo "   3. 点击 '刷新配置' 查看当前配置"
echo "   4. 输入新的数值并点击 '应用调整'"
echo "   5. 查看操作结果"
echo "=============================================================="
