# API 文档

## REST API

服务器提供 RESTful API 用于管理和监控 Modbus 数据。

### 基础 URL

```
http://localhost:8080/api
```

### 认证

如果在配置中启用了认证，需要提供 Basic Auth 或会话 Cookie。

---

## 端点

### 1. 获取从站列表

获取所有已配置的从站 ID。

**请求**

```http
GET /api/slaves
```

**响应**

```json
{
  "slaves": [1, 2]
}
```

**状态码**

- `200 OK`: 成功

---

### 2. 获取数据

获取指定从站的所有数据，或所有从站的数据。

**请求**

```http
GET /api/data?slave_id=1
```

**查询参数**

- `slave_id` (可选): 从站 ID，省略则返回所有从站数据

**响应 (单个从站)**

```json
{
  "slave_id": 1,
  "coils": [false, false, true, ...],
  "discrete_inputs": [false, false, ...],
  "holding_registers": [0, 1234, 5678, ...],
  "input_registers": [0, 0, ...]
}
```

**响应 (所有从站)**

```json
{
  "1": {
    "coils": [...],
    "discrete_inputs": [...],
    "holding_registers": [...],
    "input_registers": [...]
  },
  "2": {
    ...
  }
}
```

**状态码**

- `200 OK`: 成功
- `404 Not Found`: 从站不存在

---

### 3. 写入线圈

写入单个线圈值。

**请求**

```http
POST /api/write/coil
Content-Type: application/json

{
  "slave_id": 1,
  "address": 0,
  "value": true
}
```

**请求体**

- `slave_id` (必需): 从站 ID
- `address` (必需): 线圈地址 (0-based)
- `value` (必需): 布尔值

**响应**

```json
{
  "success": true
}
```

**状态码**

- `200 OK`: 成功
- `400 Bad Request`: 参数错误或写入失败
- `500 Internal Server Error`: 服务器错误

---

### 4. 写入寄存器

写入单个保持寄存器值。

**请求**

```http
POST /api/write/register
Content-Type: application/json

{
  "slave_id": 1,
  "address": 0,
  "value": 1234
}
```

**请求体**

- `slave_id` (必需): 从站 ID
- `address` (必需): 寄存器地址 (0-based)
- `value` (必需): 整数值 (0-65535)

**响应**

```json
{
  "success": true
}
```

**状态码**

- `200 OK`: 成功
- `400 Bad Request`: 参数错误或写入失败
- `500 Internal Server Error`: 服务器错误

---

### 5. 获取历史记录

获取数据变更历史记录。

**请求**

```http
GET /api/history?limit=100
```

**查询参数**

- `limit` (可选): 返回的最大记录数，默认 100

**响应**

```json
{
  "history": [
    {
      "timestamp": "2025-12-24T10:30:15.123456",
      "slave_id": 1,
      "data_type": "coils",
      "address": 0,
      "old_value": false,
      "new_value": true,
      "source": "web"
    },
    ...
  ]
}
```

**字段说明**

- `timestamp`: ISO 8601 格式的时间戳
- `slave_id`: 从站 ID
- `data_type`: 数据类型 (`coils`, `holding_registers`)
- `address`: 地址
- `old_value`: 旧值
- `new_value`: 新值
- `source`: 来源 (`tcp`, `rtu`, `web`)

**状态码**

- `200 OK`: 成功

---

### 6. 获取统计信息

获取服务器统计信息。

**请求**

```http
GET /api/stats
```

**响应**

```json
{
  "total_requests": 1234,
  "successful_requests": 1200,
  "function_codes": {
    "FC01": 100,
    "FC03": 500,
    "FC06": 50,
    "FC16": 150
  }
}
```

**字段说明**

- `total_requests`: 总请求数
- `successful_requests`: 成功请求数
- `function_codes`: 各功能码调用次数

**状态码**

- `200 OK`: 成功

---

### 7. 健康检查

检查服务器是否正常运行。

**请求**

```http
GET /health
```

**响应**

```json
{
  "status": "ok"
}
```

**状态码**

- `200 OK`: 服务器正常

---

## WebSocket API

服务器提供 WebSocket 连接用于实时数据推送。

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
```

### 消息格式

所有消息使用 JSON 格式。

### 客户端 → 服务器

#### 1. 订阅数据更新

```json
{
  "type": "subscribe"
}
```

**响应**

```json
{
  "type": "subscribed"
}
```

#### 2. 获取当前数据

```json
{
  "type": "get_data"
}
```

**响应**

```json
{
  "type": "data",
  "data": {
    "1": {
      "coils": [...],
      "holding_registers": [...]
    }
  }
}
```

### 服务器 → 客户端

#### 数据变化通知

当数据发生变化时，服务器会推送通知：

```json
{
  "type": "data_change",
  "slave_id": 1,
  "data_type": "coils",
  "address": 0
}
```

客户端收到通知后，可以调用 REST API 获取最新数据。

---

## 使用示例

### Python 示例

```python
import requests

base_url = "http://localhost:8080/api"

# 获取从站列表
response = requests.get(f"{base_url}/slaves")
slaves = response.json()["slaves"]
print("从站:", slaves)

# 获取数据
response = requests.get(f"{base_url}/data?slave_id=1")
data = response.json()
print("线圈:", data["coils"][:10])
print("寄存器:", data["holding_registers"][:10])

# 写入线圈
requests.post(
    f"{base_url}/write/coil",
    json={"slave_id": 1, "address": 0, "value": True}
)

# 写入寄存器
requests.post(
    f"{base_url}/write/register",
    json={"slave_id": 1, "address": 0, "value": 1234}
)

# 获取历史
response = requests.get(f"{base_url}/history?limit=10")
history = response.json()["history"]
for record in history:
    print(f"{record['timestamp']}: {record['data_type']}[{record['address']}] "
          f"{record['old_value']} → {record['new_value']}")
```

### JavaScript 示例

```javascript
// REST API
async function getData(slaveId) {
  const response = await fetch(`/api/data?slave_id=${slaveId}`);
  const data = await response.json();
  console.log('数据:', data);
  return data;
}

async function writeCoil(slaveId, address, value) {
  const response = await fetch('/api/write/coil', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slave_id: slaveId, address, value })
  });
  const result = await response.json();
  console.log('写入结果:', result);
  return result;
}

// WebSocket
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  console.log('WebSocket 已连接');
  ws.send(JSON.stringify({ type: 'subscribe' }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
  
  if (message.type === 'data_change') {
    console.log(`数据变化: 从站${message.slave_id}, ` +
                `${message.data_type}[${message.address}]`);
    // 重新加载数据
    getData(message.slave_id);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket 已断开');
  // 5秒后重连
  setTimeout(() => connectWebSocket(), 5000);
};
```

### curl 示例

```bash
# 获取从站列表
curl http://localhost:8080/api/slaves

# 获取数据
curl http://localhost:8080/api/data?slave_id=1

# 写入线圈
curl -X POST http://localhost:8080/api/write/coil \
  -H "Content-Type: application/json" \
  -d '{"slave_id":1,"address":0,"value":true}'

# 写入寄存器
curl -X POST http://localhost:8080/api/write/register \
  -H "Content-Type: application/json" \
  -d '{"slave_id":1,"address":0,"value":1234}'

# 获取历史
curl http://localhost:8080/api/history?limit=10

# 获取统计
curl http://localhost:8080/api/stats

# 健康检查
curl http://localhost:8080/health
```

---

## 错误处理

### 错误响应格式

```json
{
  "error": "错误描述"
}
```

### 常见错误

- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 错误示例

```json
{
  "error": "从站不存在"
}
```

```json
{
  "error": "写入失败"
}
```

---

## 限制

- 单次读取寄存器数量: 最多 125 个
- 单次读取线圈数量: 最多 2000 个
- 历史记录最大数量: 由配置决定（默认 1000）
- WebSocket 连接数: 无硬性限制，但建议不超过 100

---

## 版本

当前 API 版本: v1.0

API 遵循语义化版本规范。主版本号变更可能包含不兼容的更改。
