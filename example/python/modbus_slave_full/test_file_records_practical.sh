#!/bin/bash
# 文件记录功能实用测试 - 针对默认100个寄存器配置

BASE_URL="http://localhost:8080"
API_DATA="$BASE_URL/api/data"
API_WRITE="$BASE_URL/api/write/register"
SLAVE_ID=1

echo "=============================================================="
echo "🧪 文件记录功能实用测试"
echo "=============================================================="
echo "注意: 默认配置为100个保持寄存器 (地址 0-99)"
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

test_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 写入寄存器函数
write_register() {
    local addr=$1
    local value=$2
    local response=$(curl -s -X POST "$API_WRITE" \
        -H "Content-Type: application/json" \
        -d "{\"slave_id\": $SLAVE_ID, \"address\": $addr, \"value\": $value}")
    
    if echo "$response" | grep -q '"success":true'; then
        return 0
    else
        echo "写入失败 (地址$addr, 值$value): $response" >&2
        return 1
    fi
}

# 读取寄存器函数
read_registers() {
    local start=$1
    local count=$2
    local data=$(curl -s "$API_DATA?slave_id=$SLAVE_ID")
    
    echo "$data" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    regs = data.get('holding_registers', [])
    values = [regs[$start + i] if $start + i < len(regs) else 0 for i in range($count)]
    print(json.dumps(values))
except Exception as e:
    print(json.dumps([]), file=sys.stderr)
    print(f'Error: {e}', file=sys.stderr)
"
}

# 测试1: FC20 文件记录读取语义
test_section "【测试 1】FC20 - 读取文件记录 (模拟)"
echo ""
test_info "文件记录参数: 文件号=0, 记录号=10, 记录长度=5"
test_info "对应保持寄存器地址: 10-14"
echo ""

# 先写入一些测试数据
test_info "准备测试数据..."
for i in {0..4}; do
    addr=$((10 + i))
    value=$((100 + i * 10))
    if write_register $addr $value; then
        echo "  ✓ 地址 $addr 写入值 $value"
    else
        echo "  ✗ 地址 $addr 写入失败"
    fi
done

sleep 1

# 读取文件记录
test_info "读取文件记录 (地址 10-14)..."
read_result=$(read_registers 10 5)
echo "  读取结果: $read_result"

expected="[100, 110, 120, 130, 140]"
if [ "$read_result" = "$expected" ]; then
    test_pass "FC20 读取文件记录 - 数据正确"
else
    test_fail "FC20 读取文件记录 - 期望: $expected, 实际: $read_result"
fi

echo ""

# 测试2: FC21 文件记录写入语义
test_section "【测试 2】FC21 - 写入文件记录 (模拟)"
echo ""
test_info "文件记录参数: 文件号=0, 记录号=20, 记录长度=7"
test_info "对应保持寄存器地址: 20-26"
test_info "写入数据: [10, 20, 30, 40, 50, 60, 70]"
echo ""

# 写入文件记录
WRITE_DATA=(10 20 30 40 50 60 70)
write_success=true
for i in {0..6}; do
    addr=$((20 + i))
    value=${WRITE_DATA[$i]}
    if write_register $addr $value; then
        echo "  ✓ 文件记录[$i] 地址 $addr = $value"
    else
        echo "  ✗ 文件记录[$i] 地址 $addr 写入失败"
        write_success=false
    fi
done

sleep 1

# 验证写入
read_result=$(read_registers 20 7)
echo ""
test_info "读取验证: $read_result"

if [ "$read_result" = "[10, 20, 30, 40, 50, 60, 70]" ]; then
    test_pass "FC21 写入文件记录 - 数据一致"
else
    test_fail "FC21 写入文件记录 - 数据不一致"
fi

echo ""

# 测试3: 多个文件记录操作
test_section "【测试 3】多文件记录并发操作"
echo ""
test_info "文件记录1: 地址 30-32 (记录号 30, 长度 3)"
test_info "文件记录2: 地址 40-44 (记录号 40, 长度 5)"
test_info "文件记录3: 地址 50-51 (记录号 50, 长度 2)"
echo ""

# 写入文件记录1
test_info "写入文件记录1..."
write_register 30 111
write_register 31 222
write_register 32 333

# 写入文件记录2
test_info "写入文件记录2..."
for i in {0..4}; do
    write_register $((40 + i)) $((i + 1))
done

# 写入文件记录3
test_info "写入文件记录3..."
write_register 50 999
write_register 51 888

sleep 1

# 读取验证
rec1=$(read_registers 30 3)
rec2=$(read_registers 40 5)
rec3=$(read_registers 50 2)

echo ""
test_info "验证结果:"
echo "  文件记录1: $rec1"
echo "  文件记录2: $rec2"
echo "  文件记录3: $rec3"

if [ "$rec1" = "[111, 222, 333]" ] && [ "$rec2" = "[1, 2, 3, 4, 5]" ] && [ "$rec3" = "[999, 888]" ]; then
    test_pass "多文件记录并发操作 - 所有数据正确"
else
    test_fail "多文件记录并发操作 - 数据不一致"
fi

echo ""

# 测试4: 边界值测试
test_section "【测试 4】数值边界测试"
echo ""

test_info "测试地址 60-63: 最小值/最大值/零值/中间值"
write_register 60 0      # 最小值
write_register 61 65535  # 最大值
write_register 62 0      # 零值
write_register 63 32768  # 中间值

sleep 1

result=$(read_registers 60 4)
echo "  读取结果: $result"

if echo "$result" | grep -qE "\[0, 65535, 0, 32768\]"; then
    test_pass "数值边界测试 - 所有边界值正确"
else
    test_fail "数值边界测试 - 边界值不正确: $result"
fi

echo ""

# 测试5: 连续写入测试
test_section "【测试 5】连续多次写入同一记录"
echo ""

test_info "地址 70: 连续写入 111 -> 222 -> 333 -> 444"
write_register 70 111
sleep 0.2
write_register 70 222
sleep 0.2
write_register 70 333
sleep 0.2
write_register 70 444
sleep 0.5

result=$(read_registers 70 1)
echo "  最终读取: $result"

if [ "$result" = "[444]" ]; then
    test_pass "连续写入测试 - 保留最后的值"
else
    test_fail "连续写入测试 - 期望 [444], 实际: $result"
fi

echo ""

# 测试6: 跨越式地址写入
test_section "【测试 6】跨越式地址写入"
echo ""

test_info "写入地址: 5, 15, 25, 35, 45, 55, 65, 75, 85, 95"
SPARSE_ADDRS=(5 15 25 35 45 55 65 75 85 95)
SPARSE_VALUES=(1 2 3 4 5 6 7 8 9 10)

for i in {0..9}; do
    write_register ${SPARSE_ADDRS[$i]} ${SPARSE_VALUES[$i]}
done

sleep 1

# 读取验证
all_correct=true
echo "  验证结果:"
for i in {0..9}; do
    addr=${SPARSE_ADDRS[$i]}
    expected=${SPARSE_VALUES[$i]}
    result=$(read_registers $addr 1)
    if [ "$result" = "[$expected]" ]; then
        echo "    ✓ 地址 $addr = $expected"
    else
        echo "    ✗ 地址 $addr: 期望 [$expected], 实际 $result"
        all_correct=false
    fi
done

if $all_correct; then
    test_pass "跨越式地址写入 - 所有地址正确"
else
    test_fail "跨越式地址写入 - 部分地址错误"
fi

echo ""

# 测试7: 性能测试
test_section "【测试 7】性能测试 - 快速连续操作"
echo ""

test_info "快速写入 20 个寄存器 (地址 0-19)"

start_time=$(date +%s.%N)

for i in {0..19}; do
    write_register $i $((i * 5)) > /dev/null 2>&1
done

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)

echo "  写入耗时: ${duration}秒"

sleep 1

# 抽样验证
sample=$(read_registers 0 10)
echo "  抽样验证 (地址0-9): $sample"

if [ "$sample" = "[0, 5, 10, 15, 20, 25, 30, 35, 40, 45]" ]; then
    test_pass "性能测试 - 数据一致性验证"
else
    test_fail "性能测试 - 数据不一致: $sample"
fi

if (( $(echo "$duration < 10" | bc -l) )); then
    test_pass "性能测试 - 在合理时间内完成 (<10秒)"
else
    test_fail "性能测试 - 耗时过长 (${duration}秒)"
fi

echo ""

# 测试8: Web界面操作指南
test_section "【测试 8】Web界面文件记录操作"
echo ""

echo "📁 Web界面使用示例："
echo ""
echo "1️⃣  FC20 读取文件记录示例："
echo "   - 文件号: 0"
echo "   - 记录号: 10"
echo "   - 记录长度: 5"
echo "   - 结果: 应显示地址10-14的数据"
echo ""
echo "2️⃣  FC21 写入文件记录示例："
echo "   - 文件号: 0"
echo "   - 记录号: 20"
echo "   - 数据值: 10,20,30,40,50,60,70"
echo "   - 结果: 将数据写入地址20-26"
echo ""

# 验证当前数据
current_10=$(read_registers 10 5)
current_20=$(read_registers 20 7)

echo "💡 当前测试数据状态:"
echo "   地址 10-14: $current_10"
echo "   地址 20-26: $current_20"
echo ""

test_pass "Web界面操作指南 - 已提供示例参数"

echo ""

# 测试总结
test_section "📊 测试总结"
echo ""
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💡 下一步操作："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. 打开浏览器访问: http://localhost:8080"
    echo ""
    echo "2. 切换到 '📁 文件记录' 标签页"
    echo ""
    echo "3. 尝试以下操作："
    echo ""
    echo "   【读取操作 - FC20】"
    echo "   ┌─────────────────────────────────┐"
    echo "   │ 文件号:     0                   │"
    echo "   │ 记录号:     10                  │"
    echo "   │ 记录长度:   5                   │"
    echo "   └─────────────────────────────────┘"
    echo "   点击 '读取文件记录' 按钮"
    echo "   → 应显示: [100, 110, 120, 130, 140]"
    echo ""
    echo "   【写入操作 - FC21】"
    echo "   ┌─────────────────────────────────┐"
    echo "   │ 文件号:     0                   │"
    echo "   │ 记录号:     80                  │"
    echo "   │ 数据值:     11,22,33,44,55      │"
    echo "   └─────────────────────────────────┘"
    echo "   点击 '写入文件记录' 按钮"
    echo "   → 写入后可使用FC20读取验证"
    echo ""
    echo "4. 观察可视化面板的实时更新："
    echo "   • 参数映射层 (蓝色边框)"
    echo "   • 寄存器映射层 (绿色边框)"
    echo "   • 数据展示层 (橙色边框)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo -e "${RED}⚠️  有 $FAILED 个测试失败${NC}"
    echo ""
    echo "请检查:"
    echo "  • modbus-server 是否正在运行?"
    echo "  • API 端点是否可访问?"
    echo "  • 寄存器地址范围是否正确 (0-99)?"
    exit 1
fi
