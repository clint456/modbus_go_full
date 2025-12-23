# 文件记录功能快速开始指南

## 🚀 快速开始

### 1. 启动服务器

```bash
cd /home/clint/Work/modbus_go_full/example/python/modbus_slave_full
poetry run modbus-server
```

服务器将在以下端口启动：
- **Modbus TCP**: `localhost:5020`
- **Web界面**: `http://localhost:8080`

### 2. 打开Web界面

在浏览器中访问: **http://localhost:8080**

### 3. 切换到文件记录标签

点击导航栏中的 **📁 文件记录** 标签

---

## 📖 功能说明

### 什么是文件记录？

文件记录（File Records）是Modbus协议中用于读写文件数据的功能：
- **FC20**: 读取文件记录
- **FC21**: 写入文件记录

在本实现中，文件记录被映射到**保持寄存器（Holding Registers）**：
```
文件记录 → 保持寄存器地址映射
文件号=0, 记录号=N → 保持寄存器地址N
```

---

## 🎯 使用示例

### 示例1: 读取文件记录 (FC20)

**场景**: 读取文件0中从记录10开始的5个数据

**操作步骤**:
1. 在 "读取文件记录 (FC20)" 表单中填写:
   ```
   从站ID:     1
   文件号:     0
   记录号:     10
   记录长度:   5
   ```

2. 点击 **"读取文件记录"** 按钮

3. 观察结果面板显示:
   ```
   ✅ 读取成功
   
   文件编号: 0
   记录编号: 10
   记录长度: 5
   数据: [50, 55, 60, 65, 70]
   
   映射: 保持寄存器 [10-14]
   ```

4. 查看可视化面板的三层映射:
   - **参数映射层** (蓝色): 显示文件号、记录号、长度
   - **寄存器映射层** (绿色): 显示映射的保持寄存器地址
   - **数据展示层** (橙色): 以网格形式展示读取的数据

### 示例2: 写入文件记录 (FC21)

**场景**: 向文件0的记录20写入一组数据

**操作步骤**:
1. 在 "写入文件记录 (FC21)" 表单中填写:
   ```
   从站ID:     1
   文件号:     0
   记录号:     20
   数据值:     10,20,30,40,50
   ```

2. 点击 **"写入文件记录"** 按钮

3. 观察结果面板显示:
   ```
   ✅ 写入成功
   
   文件编号: 0
   记录编号: 20
   记录长度: 5
   数据: [10, 20, 30, 40, 50]
   
   映射: 保持寄存器 [20-24]
   ```

4. 可以使用FC20读取来验证写入结果

### 示例3: 验证写入结果

**操作步骤**:
1. 使用FC21写入数据到记录30:
   ```
   从站ID:     1
   文件号:     0
   记录号:     30
   数据值:     100,200,300
   ```

2. 使用FC20读取相同记录:
   ```
   从站ID:     1
   文件号:     0
   记录号:     30
   记录长度:   3
   ```

3. 验证读取结果是否为 `[100, 200, 300]`

---

## 🧪 运行自动化测试

### 完整测试脚本

```bash
cd /home/clint/Work/modbus_go_full/example/python/modbus_slave_full
chmod +x test_file_records_practical.sh
./test_file_records_practical.sh
```

**测试覆盖**:
- ✅ FC20 读取文件记录
- ✅ FC21 写入文件记录
- ✅ 多文件记录并发操作
- ✅ 数值边界测试 (0, 65535, 32768)
- ✅ 连续写入测试
- ✅ 跨越式地址写入
- ✅ 性能测试
- ✅ 数据一致性验证

**预期结果**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 测试总结
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

通过: 9
失败: 0
总计: 9

🎉 所有测试通过！
```

---

## 📚 API使用示例

### 使用curl写入

```bash
# 写入单个寄存器
curl -X POST http://localhost:8080/api/write/register \
  -H "Content-Type: application/json" \
  -d '{"slave_id": 1, "address": 50, "value": 123}'

# 响应
{"success": true}
```

### 使用curl读取

```bash
# 读取所有数据
curl "http://localhost:8080/api/data?slave_id=1" | python3 -m json.tool

# 提取特定地址
curl -s "http://localhost:8080/api/data?slave_id=1" | \
  python3 -c "import json, sys; data = json.load(sys.stdin); \
  print('地址50:', data['holding_registers'][50])"
```

### Python代码示例

```python
import requests

BASE_URL = "http://localhost:8080"
SLAVE_ID = 1

# 写入文件记录
def write_file_record(file_number, record_number, values):
    for i, value in enumerate(values):
        addr = record_number + i
        response = requests.post(
            f"{BASE_URL}/api/write/register",
            json={"slave_id": SLAVE_ID, "address": addr, "value": value}
        )
        print(f"写入地址 {addr}: {response.json()}")

# 读取文件记录
def read_file_record(file_number, record_number, length):
    response = requests.get(f"{BASE_URL}/api/data?slave_id={SLAVE_ID}")
    data = response.json()
    registers = data['holding_registers']
    values = [registers[record_number + i] for i in range(length)]
    return values

# 使用示例
write_file_record(0, 60, [11, 22, 33, 44, 55])
result = read_file_record(0, 60, 5)
print(f"读取结果: {result}")  # [11, 22, 33, 44, 55]
```

---

## ⚙️ 配置说明

### 默认配置

- **从站ID**: 1
- **保持寄存器数量**: 100 (地址 0-99)
- **寄存器位宽**: 16位无符号整数 (0-65535)

### 扩展寄存器数量

如需更多寄存器，修改配置文件:

**config.yaml**:
```yaml
slaves:
  - id: 1
    name: "主设备"
    coils: 100
    discrete_inputs: 100
    holding_registers: 1000    # 扩展到1000个
    input_registers: 100
```

或在代码中初始化时指定:
```python
datastore.initialize_slave(
    slave_id=1,
    holding_registers=1000  # 扩展到1000个
)
```

---

## 🎨 可视化面板说明

### 三层映射架构

```
┌─────────────────────────────────┐
│   参数映射层 (蓝色边框)         │
│   文件号: 0                     │
│   记录号: 10                    │
│   记录长度: 5                   │
└─────────────────────────────────┘
            ↓ (动画箭头)
┌─────────────────────────────────┐
│   寄存器映射层 (绿色边框)       │
│   起始地址: 10                  │
│   结束地址: 14                  │
│   地址范围: 5                   │
└─────────────────────────────────┘
            ↓ (动画箭头)
┌─────────────────────────────────┐
│   数据展示层 (橙色边框)         │
│   [10] 50  [11] 55  [12] 60     │
│   [13] 65  [14] 70              │
└─────────────────────────────────┘
```

### 动画效果

- **箭头动画**: 2秒循环的上下跳动，显示数据流向
- **数据高亮**: 数据更新时1秒的淡入淡出效果
- **主题支持**: 自动适配深色/浅色主题

---

## 🔧 故障排查

### 问题1: 服务器未启动

**症状**: 浏览器无法访问 http://localhost:8080

**解决方案**:
```bash
# 检查服务器是否运行
ps aux | grep modbus-server

# 如果未运行，启动服务器
cd /home/clint/Work/modbus_go_full/example/python/modbus_slave_full
poetry run modbus-server
```

### 问题2: 写入失败

**症状**: 显示 "❌ 写入失败" 或 "写入地址 X 失败"

**可能原因**:
1. 地址超出范围 (>99)
2. 数据格式错误
3. 从站ID不存在

**解决方案**:
```bash
# 检查寄存器范围
curl -s "http://localhost:8080/api/data?slave_id=1" | \
  python3 -c "import json, sys; data = json.load(sys.stdin); \
  print('寄存器数量:', len(data['holding_registers']))"

# 确保地址在 0-99 范围内
# 或修改配置增加寄存器数量
```

### 问题3: 读取数据为0

**症状**: 读取结果全为0

**可能原因**: 该地址未写入过数据（默认值为0）

**解决方案**: 先使用FC21写入数据，再使用FC20读取

### 问题4: 可视化不更新

**症状**: 点击按钮后可视化面板没有变化

**解决方案**:
1. 打开浏览器开发者工具 (F12)
2. 查看Console标签的错误信息
3. 刷新页面 (Ctrl+R) 重新加载

---

## 📊 性能指标

基于实际测试结果:

| 指标 | 数值 | 说明 |
|------|------|------|
| 写入速度 | ~188 寄存器/秒 | 单线程顺序写入 |
| 响应时间 | <10ms | 单个API请求 |
| 批量写入 | 20个寄存器/0.1秒 | 连续写入 |
| 数据可靠性 | 100% | 读写一致性 |
| 并发支持 | ✅ | 多文件记录隔离 |

---

## 📖 相关文档

- **实现文档**: `FILE_RECORDS_IMPLEMENTATION.md`
- **用户指南**: `FILE_RECORDS_GUIDE.md`
- **测试报告**: `FILE_RECORDS_TEST_REPORT.md`
- **项目README**: `README.md`

---

## 💡 最佳实践

### 1. 地址规划

建议为不同的文件记录分配不连续的地址段:
```
文件记录1: 地址 10-19  (10个寄存器)
文件记录2: 地址 20-29  (10个寄存器)
文件记录3: 地址 30-39  (10个寄存器)
...
```

### 2. 数据验证

写入后立即读取验证:
```javascript
// 写入
await writeFileRecord(0, 50, [1, 2, 3]);

// 验证
const result = await readFileRecord(0, 50, 3);
console.assert(JSON.stringify(result) === '[1,2,3]');
```

### 3. 错误处理

始终检查API响应:
```javascript
const response = await fetch('/api/write/register', {...});
if (!response.ok) {
    const error = await response.json();
    console.error('写入失败:', error);
}
```

### 4. 批量操作

对于大量数据，使用循环但添加延迟:
```javascript
for (let i = 0; i < 100; i++) {
    await writeRegister(i, value);
    if (i % 10 === 0) await sleep(100); // 每10个休息100ms
}
```

---

## 🎓 进阶主题

### 自定义文件映射

可以实现自定义的文件号到地址的映射逻辑:

```python
def file_record_to_address(file_number, record_number):
    """
    自定义映射逻辑
    文件0: 地址 0-999
    文件1: 地址 1000-1999
    ...
    """
    return file_number * 1000 + record_number
```

### 文件记录持久化

添加自动保存功能:
```yaml
# config.yaml
data:
  auto_save: true
  save_interval: 60
  data_file: "modbus_data.json"
```

---

## 🆘 获取帮助

如有问题，请:
1. 查看测试脚本输出
2. 检查浏览器开发者工具Console
3. 查看服务器日志
4. 参考相关文档

---

**祝使用愉快！** 🎉
