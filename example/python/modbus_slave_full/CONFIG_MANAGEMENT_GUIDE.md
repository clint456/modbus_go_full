# 配置管理功能使用指南

## 功能概述

配置管理功能允许您动态调整 Modbus 从站的数据块大小，无需重启服务器。支持调整以下四种数据类型：

- **线圈 (Coils)**: 范围 0-65536
- **离散输入 (Discrete Inputs)**: 范围 0-65536
- **保持寄存器 (Holding Registers)**: 范围 0-65536
- **输入寄存器 (Input Registers)**: 范围 0-65536

## Web 界面使用

### 1. 访问配置页面

1. 打开浏览器访问 `http://localhost:8080`
2. 点击导航栏的 **⚙️ 配置** 标签

### 2. 查看当前配置

点击 **刷新配置** 按钮，系统将显示：
- 从站 ID
- 线圈数量
- 离散输入数量
- 保持寄存器数量
- 输入寄存器数量

### 3. 调整数据块大小

1. 在输入框中填写要调整的数值（可以只填写需要修改的项）
2. 点击 **应用调整** 按钮
3. 查看操作结果：
   - ✅ 成功：显示绿色消息框和新的配置
   - ❌ 失败：显示红色错误消息

### 4. 使用说明

- **可选填写**：不需要填写所有字段，只填写要修改的即可
- **有效范围**：每个值必须在 0-65536 之间
- **数据保留**：调整大小时会自动保留现有数据
  - 扩大：原数据保留，新空间填充默认值
  - 缩小：保留范围内的数据，超出部分截断

## API 使用

### 获取配置

**请求：**
```bash
GET /api/config?slave_id=1
```

**响应：**
```json
{
    "slave_id": 1,
    "coils": 100,
    "discrete_inputs": 100,
    "holding_registers": 100,
    "input_registers": 100
}
```

### 调整大小

**请求：**
```bash
POST /api/config/resize
Content-Type: application/json

{
    "slave_id": 1,
    "holding_registers": 5000,
    "input_registers": 1000
}
```

**响应（成功）：**
```json
{
    "success": true,
    "slave_id": 1,
    "new_config": {
        "coils": 100,
        "discrete_inputs": 100,
        "holding_registers": 5000,
        "input_registers": 1000
    }
}
```

**响应（失败）：**
```json
{
    "error": "保持寄存器数量无效 (0-65536)"
}
```

## 命令行示例

### 示例 1：扩大保持寄存器

```bash
curl -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 5000}'
```

### 示例 2：同时调整多个类型

```bash
curl -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{
        "slave_id": 1,
        "coils": 500,
        "discrete_inputs": 500,
        "holding_registers": 10000,
        "input_registers": 2000
    }'
```

### 示例 3：查看当前配置

```bash
curl -s "http://localhost:8080/api/config?slave_id=1" | python3 -m json.tool
```

## 常见场景

### 场景 1：存储长字符串

**问题**：需要写入超过 100 个字符的字符串（默认只有 100 个寄存器）

**解决方案**：
```bash
# 1. 扩大保持寄存器到 1000
curl -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 1000}'

# 2. 现在可以写入长字符串了
curl -X POST http://localhost:8080/api/write/string \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "address": 100, "text": "很长的字符串内容..."}'
```

### 场景 2：测试大数据量

**问题**：需要测试系统对大量数据点的处理能力

**解决方案**：
```bash
# 扩大到最大值
curl -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 65536}'
```

### 场景 3：节省内存

**问题**：实际只使用了少量寄存器，想节省内存

**解决方案**：
```bash
# 缩小到实际需要的大小
curl -X POST http://localhost:8080/api/config/resize \
    -H "Content-Type: application/json" \
    -d '{"slave_id": 1, "holding_registers": 50}'
```

## 重要提示

### ✅ 支持的操作
- 动态扩大数据块
- 动态缩小数据块
- 同时调整多种数据类型
- 数据自动保留

### ⚠️ 注意事项
- 调整操作会立即生效
- 缩小时超出范围的数据会被截断
- 有效范围：0-65536
- 修改会自动保存到数据文件

### 💡 最佳实践
1. **先查看当前配置**：了解当前状态
2. **按需调整**：只修改需要的字段
3. **验证结果**：检查返回的新配置
4. **测试功能**：确认数据操作正常

## 测试脚本

### 快速演示
运行内置的演示脚本：
```bash
./demo_config_management.sh
```

### 完整测试
运行完整的测试套件：
```bash
./test_config_management.sh
```

测试包含：
1. ✅ 获取当前配置
2. ✅ 扩大保持寄存器大小
3. ✅ 验证数据保留
4. ✅ 写入扩展区域
5. ✅ 写入长字符串
6. ✅ 同时调整多个类型
7. ✅ 边界测试（最大值）
8. ✅ 边界测试（超出范围）
9. ✅ 缩小寄存器测试
10. ✅ 数据保留验证

## 故障排除

### 问题：API 返回 404
**原因**：服务器未启动或路由未加载
**解决**：重启服务器
```bash
poetry run modbus-server
```

### 问题：调整后数据丢失
**原因**：缩小到的大小小于数据地址
**解决**：确保新大小大于最高数据地址

### 问题：超出范围错误
**原因**：输入值不在 0-65536 范围内
**解决**：检查输入值，使用有效范围

## 技术细节

### 实现原理
- 使用 Python 列表动态调整大小
- 数据拷贝：`new_data[:min(old_len, new_len)] = old_data[:min(old_len, new_len)]`
- 自动设置修改标志触发保存

### 性能影响
- 扩大操作：O(n) - 需要复制现有数据
- 缩小操作：O(n) - 需要复制保留的数据
- 内存影响：与数据块大小成正比

### 数据持久化
- 修改后自动标记为已修改
- 根据配置自动保存到 JSON 文件
- 重启后自动加载保存的配置

## 相关功能

- [快速入门指南](QUICK_START.md)
- [字符串操作指南](STRING_OPERATIONS_GUIDE.md)
- [文件记录指南](FILE_RECORDS_GUIDE.md)
