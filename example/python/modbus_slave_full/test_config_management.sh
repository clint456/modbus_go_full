#!/bin/bash

echo "=============================================================="
echo "⚙️  配置管理功能测试"
echo "=============================================================="
echo ""

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0

# 测试函数
test_case() {
    local test_name="$1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "【测试 $TOTAL_TESTS】$test_name"
    echo "--------------------------------------------------------------"
}

pass_test() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "  ✅ 测试通过"
    echo ""
}

fail_test() {
    echo "  ❌ 测试失败: $1"
    echo ""
}

# 测试 1: 获取当前配置
test_case "获取当前配置"
response=$(curl -s "http://localhost:8080/api/config?slave_id=1")
echo "  响应: $response"

if echo "$response" | grep -q "slave_id"; then
    coils=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['coils'])")
    discrete=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['discrete_inputs'])")
    holding=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['holding_registers'])")
    input=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['input_registers'])")
    
    echo "  当前配置:"
    echo "    • 线圈: $coils"
    echo "    • 离散输入: $discrete"
    echo "    • 保持寄存器: $holding"
    echo "    • 输入寄存器: $input"
    pass_test
else
    fail_test "无法获取配置信息"
fi

# 测试 2: 写入测试数据（地址 90-99）
test_case "写入测试数据到保持寄存器 90-99"
for i in {90..99}; do
    value=$((1000 + i))
    curl -s -X POST http://localhost:8080/api/write/register \
        -H "Content-Type: application/json" \
        -d "{\"slave_id\": 1, \"address\": $i, \"value\": $value}" > /dev/null
    echo -n "."
done
echo ""
echo "  ✓ 已写入 10 个测试数据"
pass_test

# 测试 3: 扩大保持寄存器到 500
test_case "扩大保持寄存器大小 (100 → 500)"
response=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 500}')

echo "  响应: $response"

if echo "$response" | grep -q "new_config"; then
    new_size=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['holding_registers'])")
    echo "  新的保持寄存器大小: $new_size"
    
    if [ "$new_size" -eq 500 ]; then
        pass_test
    else
        fail_test "大小调整不正确"
    fi
else
    fail_test "调整失败"
fi

# 测试 4: 验证数据保留
test_case "验证数据保留（地址 90-99 的数据应该还在）"
data_response=$(curl -s "http://localhost:8080/api/data?slave_id=1")

preserved=true
for i in {90..99}; do
    expected=$((1000 + i))
    actual=$(echo "$data_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['holding_registers'][$i] if $i < len(data['holding_registers']) else 0)")
    
    if [ "$actual" -eq "$expected" ]; then
        echo "  ✓ 地址 $i: $actual (正确)"
    else
        echo "  ✗ 地址 $i: 期望 $expected, 实际 $actual"
        preserved=false
    fi
done

if [ "$preserved" = true ]; then
    pass_test
else
    fail_test "数据未正确保留"
fi

# 测试 5: 写入数据到扩展区域（地址 200-204）
test_case "写入数据到扩展区域（地址 200-204）"
for i in {200..204}; do
    value=$((2000 + i))
    result=$(curl -s -X POST http://localhost:8080/api/write/register \
        -H "Content-Type: application/json" \
        -d "{\"slave_id\": 1, \"address\": $i, \"value\": $value}")
    echo -n "."
done
echo ""

# 验证写入
data_response=$(curl -s "http://localhost:8080/api/data?slave_id=1")
value_200=$(echo "$data_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['holding_registers'][200] if 200 < len(data['holding_registers']) else 0)")

if [ "$value_200" -eq 2200 ]; then
    echo "  ✓ 扩展区域可以正常写入"
    pass_test
else
    fail_test "扩展区域写入失败"
fi

# 测试 6: 写入长字符串（利用扩展空间）
test_case "写入长字符串到扩展区域（100+ 寄存器）"
long_string="这是一个很长的测试字符串，用来验证动态调整大小后可以存储更大的数据。Dynamic resizing allows for larger data storage capacity!"

result=$(curl -s -X POST http://localhost:8080/api/write/string \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": 1, \"address\": 300, \"text\": \"$long_string\"}")

echo "  写入响应: $result"

if echo "$result" | grep -q "success"; then
    registers_used=$(echo "$result" | python3 -c "import json, sys; print(json.load(sys.stdin)['registers_written'])")
    echo "  使用了 $registers_used 个寄存器"
    
    # 读取回来验证
    read_result=$(curl -s "http://localhost:8080/api/read/string?slave_id=1&address=300&count=$registers_used")
    read_text=$(echo "$read_result" | python3 -c "import json, sys; print(json.load(sys.stdin).get('text', ''))")
    
    if [ "$read_text" = "$long_string" ]; then
        echo "  ✓ 字符串读写一致"
        pass_test
    else
        fail_test "字符串读取不一致"
    fi
else
    fail_test "字符串写入失败"
fi

# 测试 7: 调整多个数据类型
test_case "同时调整多个数据类型"
response=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "coils": 200, "discrete_inputs": 200, "input_registers": 300}')

echo "  响应: $response"

if echo "$response" | grep -q "new_config"; then
    coils=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['coils'])")
    discrete=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['discrete_inputs'])")
    input=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['input_registers'])")
    
    echo "  新配置:"
    echo "    • 线圈: $coils"
    echo "    • 离散输入: $discrete"
    echo "    • 输入寄存器: $input"
    
    if [ "$coils" -eq 200 ] && [ "$discrete" -eq 200 ] && [ "$input" -eq 300 ]; then
        pass_test
    else
        fail_test "配置调整不正确"
    fi
else
    fail_test "调整失败"
fi

# 测试 8: 边界测试 - 最大值
test_case "边界测试：设置最大值 (65536)"
response=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 65536}')

if echo "$response" | grep -q "new_config"; then
    size=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['holding_registers'])")
    echo "  设置成功: $size"
    pass_test
else
    fail_test "最大值设置失败"
fi

# 测试 9: 边界测试 - 超出范围
test_case "边界测试：超出范围值 (65537) - 应该失败"
response=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 65537}')

if echo "$response" | grep -q "error"; then
    echo "  预期的错误: $response"
    pass_test
else
    fail_test "应该拒绝超出范围的值"
fi

# 测试 10: 缩小寄存器测试
test_case "缩小寄存器大小 (65536 → 1000)"
response=$(curl -s -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 1000}')

if echo "$response" | grep -q "new_config"; then
    size=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['new_config']['holding_registers'])")
    echo "  调整后大小: $size"
    
    # 验证之前的数据（地址 90-99 和 200-204）仍然保留
    data_response=$(curl -s "http://localhost:8080/api/data?slave_id=1")
    value_90=$(echo "$data_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['holding_registers'][90] if 90 < len(data['holding_registers']) else 0)")
    value_200=$(echo "$data_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['holding_registers'][200] if 200 < len(data['holding_registers']) else 0)")
    
    if [ "$value_90" -eq 1090 ] && [ "$value_200" -eq 2200 ]; then
        echo "  ✓ 缩小后数据仍然保留"
        pass_test
    else
        fail_test "缩小后数据丢失"
    fi
else
    fail_test "缩小操作失败"
fi

# 最终报告
echo "=============================================================="
echo "📊 测试总结"
echo "=============================================================="
echo ""
echo "  总测试数: $TOTAL_TESTS"
echo "  通过: $PASSED_TESTS"
echo "  失败: $((TOTAL_TESTS - PASSED_TESTS))"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "  🎉 所有测试通过！"
    echo ""
    echo "  💡 现在可以在 Web 界面测试："
    echo "     1. 访问 http://localhost:8080"
    echo "     2. 切换到 '⚙️ 配置' 标签页"
    echo "     3. 点击 '刷新配置' 查看当前配置"
    echo "     4. 尝试调整寄存器大小"
else
    echo "  ⚠️  部分测试失败，请检查日志"
fi

echo "=============================================================="
