#!/bin/bash
# 文件记录功能全面测试脚本

BASE_URL="http://localhost:8080"
API_DATA="$BASE_URL/api/data"
API_WRITE="$BASE_URL/api/write/register"
SLAVE_ID=1

echo "=============================================================="
echo "🧪 文件记录功能全面测试"
echo "=============================================================="
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果函数
test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

test_info() {
    echo -e "${YELLOW}ℹ️  INFO${NC}: $1"
}

# 写入寄存器函数
write_register() {
    local addr=$1
    local value=$2
    local response=$(curl -s -X POST "$API_WRITE" \
        -H "Content-Type: application/json" \
        -d "{\"slave_id\": $SLAVE_ID, \"address\": $addr, \"value\": $value}")
    
    if echo "$response" | grep -q '"status":"success"'; then
        return 0
    else
        echo "写入失败: $response"
        return 1
    fi
}

# 读取寄存器函数
read_registers() {
    local start=$1
    local count=$2
    local data=$(curl -s "$API_DATA?slave_id=$SLAVE_ID")
    
    # 提取保持寄存器数据（返回的是列表不是字典）
    echo "$data" | python3 -c "
import json, sys
data = json.load(sys.stdin)
regs = data.get('holding_registers', [])
values = [regs[$start + i] if $start + i < len(regs) else 0 for i in range($count)]
print(json.dumps(values))
"
}

# 测试1: 基本写入和读取
echo "【测试 1】基本文件记录写入和读取"
echo "--------------------------------------------------------------"
test_info "写入文件记录到地址 100-104"

# 写入测试数据
TEST_DATA=(10 20 30 40 50)
for i in {0..4}; do
    addr=$((100 + i))
    value=${TEST_DATA[$i]}
    if write_register $addr $value; then
        echo "  ✓ 地址 $addr = $value"
    else
        test_fail "写入地址 $addr 失败"
    fi
done

sleep 1

# 读取并验证
test_info "读取文件记录地址 100-104"
read_result=$(read_registers 100 5)
echo "  读取结果: $read_result"

expected="[10, 20, 30, 40, 50]"
if [ "$read_result" = "$expected" ]; then
    test_pass "基本读写测试 - 数据一致"
else
    test_fail "基本读写测试 - 数据不一致 (期望: $expected, 实际: $read_result)"
fi

echo ""

# 测试2: 大数值测试
echo "【测试 2】大数值边界测试"
echo "--------------------------------------------------------------"
test_info "写入大数值到地址 200-202"

# 写入边界值
write_register 200 0      # 最小值
write_register 201 32767  # 有符号最大正值
write_register 202 65535  # 无符号最大值

sleep 1

read_result=$(read_registers 200 3)
echo "  读取结果: $read_result"

if echo "$read_result" | grep -q "0.*32767.*65535"; then
    test_pass "大数值边界测试"
else
    test_fail "大数值边界测试 - 数据不匹配"
fi

echo ""

# 测试3: 连续多次写入
echo "【测试 3】连续多次写入同一地址"
echo "--------------------------------------------------------------"
test_info "连续写入地址 300: 111 -> 222 -> 333"

write_register 300 111
sleep 0.5
write_register 300 222
sleep 0.5
write_register 300 333
sleep 0.5

read_result=$(read_registers 300 1)
echo "  最终读取结果: $read_result"

if [ "$read_result" = "[333]" ]; then
    test_pass "连续写入测试 - 保留最后写入的值"
else
    test_fail "连续写入测试 - 值不正确 (期望: [333], 实际: $read_result)"
fi

echo ""

# 测试4: 跨越不同地址范围
echo "【测试 4】不同地址范围测试"
echo "--------------------------------------------------------------"
test_info "测试地址范围: 0, 1000, 5000, 9999"

write_register 0 100
write_register 1000 200
write_register 5000 300
write_register 9999 400

sleep 1

result_0=$(read_registers 0 1)
result_1000=$(read_registers 1000 1)
result_5000=$(read_registers 5000 1)
result_9999=$(read_registers 9999 1)

echo "  地址 0: $result_0"
echo "  地址 1000: $result_1000"
echo "  地址 5000: $result_5000"
echo "  地址 9999: $result_9999"

if [ "$result_0" = "[100]" ] && [ "$result_1000" = "[200]" ] && \
   [ "$result_5000" = "[300]" ] && [ "$result_9999" = "[400]" ]; then
    test_pass "不同地址范围测试"
else
    test_fail "不同地址范围测试 - 某些地址数据不正确"
fi

echo ""

# 测试5: 文件记录语义测试（模拟FC21写入）
echo "【测试 5】文件记录语义测试"
echo "--------------------------------------------------------------"
test_info "模拟文件记录: 文件0, 记录50, 长度5"

# 文件记录映射: 文件0的记录50 -> 保持寄存器 50-54
FILE_NUMBER=0
RECORD_NUMBER=50
RECORD_LENGTH=5

BASE_ADDR=$((FILE_NUMBER * 10000 + RECORD_NUMBER))
test_info "计算的基地址: $BASE_ADDR"

# 写入文件记录数据
RECORD_DATA=(11 22 33 44 55)
for i in $(seq 0 $((RECORD_LENGTH - 1))); do
    addr=$((BASE_ADDR + i))
    value=${RECORD_DATA[$i]}
    write_register $addr $value
    echo "  ✓ 文件记录[$i] 地址 $addr = $value"
done

sleep 1

# 读取文件记录
read_result=$(read_registers $BASE_ADDR $RECORD_LENGTH)
echo "  读取文件记录: $read_result"

if [ "$read_result" = "[11, 22, 33, 44, 55]" ]; then
    test_pass "文件记录语义测试"
else
    test_fail "文件记录语义测试 - 数据不一致"
fi

echo ""

# 测试6: 零值测试
echo "【测试 6】零值写入测试"
echo "--------------------------------------------------------------"
test_info "写入零值到地址 400-404"

for i in {0..4}; do
    addr=$((400 + i))
    write_register $addr 0
done

sleep 1

read_result=$(read_registers 400 5)
echo "  读取结果: $read_result"

if [ "$read_result" = "[0, 0, 0, 0, 0]" ]; then
    test_pass "零值写入测试"
else
    test_fail "零值写入测试 - 数据不正确"
fi

echo ""

# 测试7: 交替模式写入
echo "【测试 7】交替模式写入测试"
echo "--------------------------------------------------------------"
test_info "写入交替模式到地址 500-509"

for i in {0..9}; do
    addr=$((500 + i))
    value=$((i % 2 == 0 ? 100 : 200))
    write_register $addr $value
done

sleep 1

read_result=$(read_registers 500 10)
echo "  读取结果: $read_result"

if echo "$read_result" | grep -qE "\[100, 200, 100, 200, 100, 200, 100, 200, 100, 200\]"; then
    test_pass "交替模式写入测试"
else
    test_fail "交替模式写入测试 - 模式不匹配"
fi

echo ""

# 测试8: API响应格式验证
echo "【测试 8】API响应格式验证"
echo "--------------------------------------------------------------"

# 测试读取API
read_response=$(curl -s "$API_DATA?slave_id=$SLAVE_ID")
echo "  读取API响应示例:"
echo "$read_response" | python3 -m json.tool | head -20

if echo "$read_response" | python3 -c "import json, sys; json.load(sys.stdin); exit(0)" 2>/dev/null; then
    test_pass "读取API返回有效JSON"
else
    test_fail "读取API返回无效JSON"
fi

# 测试写入API
write_response=$(curl -s -X POST "$API_WRITE" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": 999, \"value\": 888}")

echo "  写入API响应: $write_response"

if echo "$write_response" | grep -q '"status":"success"'; then
    test_pass "写入API返回成功状态"
else
    test_fail "写入API返回失败或格式错误"
fi

echo ""

# 测试9: 性能测试（快速写入）
echo "【测试 9】性能测试 - 快速连续写入"
echo "--------------------------------------------------------------"
test_info "快速写入100个寄存器"

start_time=$(date +%s.%N)

for i in {1..100}; do
    write_register $((600 + i - 1)) $i > /dev/null 2>&1
done

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)

echo "  写入100个寄存器耗时: ${duration}秒"

if (( $(echo "$duration < 30" | bc -l) )); then
    test_pass "性能测试 - 在合理时间内完成"
else
    test_fail "性能测试 - 耗时过长"
fi

sleep 1

# 验证部分数据
sample_result=$(read_registers 600 5)
echo "  抽样验证(地址600-604): $sample_result"

if [ "$sample_result" = "[1, 2, 3, 4, 5]" ]; then
    test_pass "性能测试 - 数据一致性验证"
else
    test_fail "性能测试 - 数据一致性验证失败"
fi

echo ""

# 测试总结
echo "=============================================================="
echo "📊 测试总结"
echo "=============================================================="
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    echo ""
    echo "💡 提示："
    echo "  1. 访问 http://localhost:8080"
    echo "  2. 切换到 '📁 文件记录' 标签页"
    echo "  3. 尝试以下操作："
    echo "     - 文件号: 0, 记录号: 50, 长度: 5 (读取)"
    echo "     - 文件号: 0, 记录号: 100, 数据: 10,20,30,40,50 (写入)"
    exit 0
else
    echo -e "${RED}⚠️  有测试失败，请检查日志${NC}"
    exit 1
fi
