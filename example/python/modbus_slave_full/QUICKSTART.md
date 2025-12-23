# 快速启动指南

## 5分钟快速开始

### 方式 1: 使用 Poetry (推荐)

```bash
# 1. 安装依赖
poetry install

# 2. 运行服务器
poetry run modbus-server
```

### 方式 2: 使用 Docker

```bash
# 1. 复制配置文件
cp config.example.yaml config.yaml

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

## 访问服务

启动后，你可以访问：

- **Web 控制台**: http://localhost:8080
- **Modbus TCP**: localhost:5020
- **API**: http://localhost:8080/api

默认登录凭证（如果启用了认证）：
- 用户名: `admin`
- 密码: `admin123`

## 测试连接

### 使用 curl 测试 API

```bash
# 获取从站列表
curl http://localhost:8080/api/slaves

# 获取数据
curl http://localhost:8080/api/data?slave_id=1

# 健康检查
curl http://localhost:8080/health
```

### 使用 Python 测试 Modbus TCP

```python
from pymodbus.client import ModbusTcpClient

# 连接到服务器
client = ModbusTcpClient('localhost', port=5020)

# 读取保持寄存器
result = client.read_holding_registers(0, 10, slave=1)
if not result.isError():
    print("寄存器值:", result.registers)

# 写入寄存器
client.write_register(0, 1234, slave=1)

# 读取线圈
result = client.read_coils(0, 10, slave=1)
if not result.isError():
    print("线圈值:", result.bits)

client.close()
```

## 配置

编辑 `config.yaml` 自定义配置：

```yaml
server:
  tcp:
    port: 5020
  
slaves:
  - id: 1
    name: "我的设备"
    coils: 100
    holding_registers: 100

web:
  port: 8080
```

## 停止服务

### Poetry 方式

按 `Ctrl+C` 停止服务器

### Docker 方式

```bash
docker-compose down
```

## 下一步

- 阅读 [完整文档](README.md)
- 查看 [配置指南](docs/configuration.md)
- 浏览 [API 文档](docs/api.md)

## 常见问题

**Q: 端口被占用怎么办？**

A: 修改 `config.yaml` 中的端口号。

**Q: 如何添加多个从站？**

A: 在 `config.yaml` 的 `slaves` 部分添加更多从站配置。

**Q: 如何启用 RTU 模式？**

A: 在 `config.yaml` 中设置 `server.rtu.enabled: true` 并配置串口参数。
