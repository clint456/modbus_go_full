#!/bin/bash
# 字符串读写功能测试脚本

BASE_URL="http://localhost:8080"
API_WRITE_STRING="$BASE_URL/api/write/string"
API_READ_STRING="$BASE_URL/api/read/string"
SLAVE_ID=1

echo "=============================================================="
echo "📝 字符串读写功能测试"
echo "=============================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
}

test_info() {
    echo -e "${YELLOW}ℹ️  INFO${NC}: $1"
}

test_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 测试1: 写入简单字符串
test_section "【测试 1】写入简单字符串"
echo ""

TEXT1="Hello"
ADDR1=0

test_info "写入字符串: \"$TEXT1\" 到地址 $ADDR1"

response=$(curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR1, \"text\": \"$TEXT1\"}")

echo "响应: $response" | python3 -m json.tool

if echo "$response" | grep -q '"success"'; then
    test_pass "写入字符串成功"
else
    test_fail "写入字符串失败"
fi

echo ""

# 测试2: 读取字符串
test_section "【测试 2】读取字符串"
echo ""

test_info "从地址 $ADDR1 读取字符串 (长度: 3 个寄存器)"

response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR1&length=3")

echo "响应: $response" | python3 -m json.tool
echo ""

read_text=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])" 2>/dev/null)

if [ "$read_text" = "$TEXT1" ]; then
    test_pass "读取字符串正确: \"$read_text\""
else
    test_fail "读取字符串不匹配 (期望: \"$TEXT1\", 实际: \"$read_text\")"
fi

echo ""

# 测试3: 写入中文字符串
test_section "【测试 3】写入中文字符串"
echo ""

TEXT2="你好世界"
ADDR2=10

test_info "写入中文字符串: \"$TEXT2\" 到地址 $ADDR2"

response=$(curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR2, \"text\": \"$TEXT2\"}")

echo "响应: $response" | python3 -m json.tool

if echo "$response" | grep -q '"success"'; then
    test_pass "写入中文字符串成功"
else
    test_fail "写入中文字符串失败"
fi

echo ""

# 读取验证
test_info "读取中文字符串验证"
response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR2&length=2")
read_text=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])" 2>/dev/null)

if [ "$read_text" = "$TEXT2" ]; then
    test_pass "中文字符串读取正确: \"$read_text\""
else
    test_fail "中文字符串读取不匹配"
fi

echo ""

# 测试4: 长字符串
test_section "【测试 4】写入长字符串"
echo ""

TEXT3="Modbus TCP Server with String Support!"
ADDR3=20

test_info "写入长字符串 (${#TEXT3} 字符)"
test_info "文本: \"$TEXT3\""

response=$(curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR3, \"text\": \"$TEXT3\"}")

regs_written=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('registers_written', 0))" 2>/dev/null)

echo "写入寄存器数: $regs_written"

if [ "$regs_written" -gt 0 ]; then
    test_pass "长字符串写入成功 (使用 $regs_written 个寄存器)"
else
    test_fail "长字符串写入失败"
fi

echo ""

# 读取验证
test_info "读取长字符串验证 (长度: $regs_written 个寄存器)"
response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR3&length=$regs_written")
read_text=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])" 2>/dev/null)

if [ "$read_text" = "$TEXT3" ]; then
    test_pass "长字符串读取正确"
else
    test_fail "长字符串读取不匹配"
    echo "  期望: \"$TEXT3\""
    echo "  实际: \"$read_text\""
fi

echo ""

# 测试5: 特殊字符
test_section "【测试 5】特殊字符测试"
echo ""

TEXT4="123!@#$%"
ADDR4=40

test_info "写入特殊字符: \"$TEXT4\""

response=$(curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR4, \"text\": \"$TEXT4\"}")

if echo "$response" | grep -q '"success"'; then
    test_pass "特殊字符写入成功"
else
    test_fail "特殊字符写入失败"
fi

# 读取验证
response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR4&length=5")
read_text=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])" 2>/dev/null)

if [ "$read_text" = "$TEXT4" ]; then
    test_pass "特殊字符读取正确"
else
    test_fail "特殊字符读取不匹配"
fi

echo ""

# 测试6: 奇数长度字符串
test_section "【测试 6】奇数长度字符串"
echo ""

TEXT5="ABC"
ADDR5=50

test_info "写入奇数长度字符串: \"$TEXT5\" (3个字符)"

response=$(curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR5, \"text\": \"$TEXT5\"}")

regs_written=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('registers_written', 0))" 2>/dev/null)

echo "写入寄存器数: $regs_written"

if [ "$regs_written" = "2" ]; then
    test_pass "奇数长度字符串使用了2个寄存器"
else
    test_fail "奇数长度字符串寄存器数不正确"
fi

# 读取验证
response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR5&length=2")
read_text=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])" 2>/dev/null)

if [ "$read_text" = "$TEXT5" ]; then
    test_pass "奇数长度字符串读取正确"
else
    test_fail "奇数长度字符串读取不匹配"
fi

echo ""

# 测试7: 查看寄存器编码
test_section "【测试 7】查看字符串编码"
echo ""

TEXT6="Hi"
ADDR6=60

test_info "写入字符串: \"$TEXT6\""
curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR6, \"text\": \"$TEXT6\"}" > /dev/null

sleep 1

test_info "读取并显示编码详情"
response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR6&length=1")

echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  文本: \"{data[\"text\"]}\"')
print(f'  寄存器值: {data[\"registers\"]}')
for i, reg in enumerate(data['registers']):
    high = (reg >> 8) & 0xFF
    low = reg & 0xFF
    print(f'  寄存器[{ADDR6 + i}]: 0x{reg:04X} = 高字节=0x{high:02X}(\"{chr(high) if high else \"\\\\0\"}\") + 低字节=0x{low:02X}(\"{chr(low) if low else \"\\\\0\"}\")')
"

test_pass "编码显示完成"

echo ""

# 测试8: 覆盖写入
test_section "【测试 8】覆盖写入测试"
echo ""

ADDR7=70

test_info "第一次写入: \"AAAA\""
curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR7, \"text\": \"AAAA\"}" > /dev/null

sleep 1

response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR7&length=2")
text1=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])")
echo "  读取结果: \"$text1\""

test_info "第二次写入(覆盖): \"BB\""
curl -s -X POST "$API_WRITE_STRING" \
    -H "Content-Type: application/json" \
    -d "{\"slave_id\": $SLAVE_ID, \"address\": $ADDR7, \"text\": \"BB\"}" > /dev/null

sleep 1

response=$(curl -s "$API_READ_STRING?slave_id=$SLAVE_ID&address=$ADDR7&length=2")
text2=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin)['text'])")
echo "  读取结果: \"$text2\""

if [[ "$text2" == "BB"* ]]; then
    test_pass "覆盖写入成功"
else
    test_fail "覆盖写入失败"
fi

echo ""

# 总结
test_section "📊 测试总结"
echo ""

echo "✅ 所有字符串读写功能测试完成！"
echo ""
echo "🎯 功能特性:"
echo "  • 支持ASCII字符串读写"
echo "  • 支持中文字符(UTF-8编码)"
echo "  • 每2个字符占用1个寄存器(16位)"
echo "  • 自动处理奇数长度字符串"
echo "  • 高字节存储第1个字符，低字节存储第2个字符"
echo ""
echo "💡 使用方式:"
echo "  1. Web界面: http://localhost:8080"
echo "  2. 切换到 '📁 文件记录' 标签"
echo "  3. 使用 '📝 写入字符串' 和 '📖 读取字符串' 表单"
echo ""
echo "📝 API示例:"
echo "  # 写入"
echo "  curl -X POST http://localhost:8080/api/write/string \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"slave_id\": 1, \"address\": 0, \"text\": \"Hello\"}'"
echo ""
echo "  # 读取"
echo "  curl 'http://localhost:8080/api/read/string?slave_id=1&address=0&length=3'"
echo ""
echo "=============================================================="
