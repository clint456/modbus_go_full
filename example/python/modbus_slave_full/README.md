# Modbus 服务器

功能完整的 Modbus TCP/RTU 服务器，**支持功能码 FC01-24**，包含 Web 控制台。

## ✨ 特性

- 🔌 **完整功能码支持**: FC01-24 (18个功能码)，包括文件记录操作
- 🔧 **Modbus TCP/RTU**: 完整的 TCP 和 RTU 协议实现
- 🌐 **Web 控制台**: 现代化的 Web 界面，实时监控和控制
- 💾 **数据持久化**: 自动保存和加载数据
- 📊 **历史记录**: 记录所有数据变更
- 📈 **统计信息**: 功能码调用统计和成功率
- 🔄 **WebSocket 实时推送**: 数据变化实时通知
- 🌓 **暗黑模式**: 支持明亮/暗黑主题切换
- 🧪 **完整测试**: 31 个单元测试 + 集成测试，100% 通过

## 📋 支持的功能码

| 功能码 | 描述 | 状态 |
|-------|------|------|
| FC01 (0x01) | 读线圈 | ✅ |
| FC02 (0x02) | 读离散输入 | ✅ |
| FC03 (0x03) | 读保持寄存器 | ✅ |
| FC04 (0x04) | 读输入寄存器 | ✅ |
| FC05 (0x05) | 写单个线圈 | ✅ |
| FC06 (0x06) | 写单个寄存器 | ✅ |
| FC07 (0x07) | 读异常状态 | ✅ |
| FC08 (0x08) | 诊断 | ✅ |
| FC11 (0x0B) | 获取通信事件计数器 | ✅ |
| FC12 (0x0C) | 获取通信事件日志 | ✅ |
| FC15 (0x0F) | 写多个线圈 | ✅ |
| FC16 (0x10) | 写多个寄存器 | ✅ |
| FC17 (0x11) | 报告从站ID | ✅ |
| FC20 (0x14) | 读文件记录 | ✅ |
| FC21 (0x15) | 写文件记录 | ✅ |
| FC22 (0x16) | 屏蔽写寄存器 | ✅ |
| FC23 (0x17) | 读写多个寄存器 | ✅ |
| FC24 (0x18) | 读FIFO队列 | ✅ |

**共计 18 个功能码，全部实现并测试通过！**

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Poetry (推荐) 或 pip

### 使用 Poetry 安装

```bash
# 克隆项目
cd modbus-slave-full

# 安装依赖
poetry install

# 运行服务器
poetry run modbus-server

# 或者激活虚拟环境后运行
poetry shell
modbus-server
```

### 使用 pip 安装

```bash
# 安装依赖
pip install aiohttp pyserial-asyncio pyyaml aiohttp-cors

# 运行服务器
python -m modbus_slave_full
```

### 使用 Docker

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

## 📖 配置

创建 `config.yaml` 文件（可以从 `config.example.yaml` 复制）：

```yaml
server:
  tcp:
    enabled: true
    host: "0.0.0.0"
    port: 5020
  rtu:
    enabled: false
    port: "/dev/ttyUSB0"
    baudrate: 9600

slaves:
  - id: 1
    name: "主设备"
    coils: 100
    holding_registers: 100

web:
  enabled: true
  host: "0.0.0.0"
  port: 8080

data:
  auto_save: true
  save_interval: 60
  data_file: "modbus_data.json"

logging:
  level: "INFO"
  file: "modbus_server.log"
```

## � Web 控制台

启动服务器后，访问 `http://localhost:8080` 打开 Web 控制台。

### 功能

- **数据监控**: 实时查看和修改线圈、寄存器值
- **📁 文件记录**: 可视化操作文件记录功能（FC20/FC21）⭐ 新增
- **历史记录**: 查看所有数据变更历史
- **统计信息**: 查看功能码调用统计
- **WebSocket**: 实时数据推送
- **暗黑模式**: 切换主题

### 文件记录可视化界面 ⭐

新增的**文件记录**标签页提供直观的界面展示文件记录操作：

- 🗺️ **映射关系可视化**: 三层流程图展示文件记录如何映射到保持寄存器
- 📖 **读取操作 (FC20)**: 可视化读取过程和结果
- ✍️ **写入操作 (FC21)**: 实时显示写入过程
- 📊 **数据网格**: 动态显示寄存器地址和值
- 💡 **工作原理说明**: 详细解释映射机制

详见: [文件记录使用指南](FILE_RECORDS_GUIDE.md)

## 🧪 测试

```bash
# 运行所有测试 (31个测试用例)
poetry run pytest

# 运行测试并显示详细信息
poetry run pytest -v

# 运行特定测试文件
poetry run pytest tests/test_advanced_functions.py

# 运行完整功能测试客户端
poetry run python test_client.py
```

### 测试覆盖
- ✅ 数据存储测试 (9 个)
- ✅ 协议功能测试 (7 个)
- ✅ Web API 测试 (5 个)
- ✅ 高级功能测试 (10 个)
- ✅ 集成测试 (18 个功能码)

## 📝 开发

### 代码格式化

```bash
# 使用 Black 格式化代码
poetry run black modbus_slave_full tests

# 使用 isort 整理导入
poetry run isort modbus_slave_full tests
```

### 类型检查

```bash
# 使用 mypy 进行类型检查
poetry run mypy modbus_slave_full
```

### 代码检查

```bash
# 使用 flake8 检查代码
poetry run flake8 modbus_slave_full tests
```

## 📚 API 文档

### REST API

#### 获取从站列表
```
GET /api/slaves
```

#### 获取数据
```
GET /api/data?slave_id=1
```

#### 写入线圈
```
POST /api/write/coil
Content-Type: application/json

{
  "slave_id": 1,
  "address": 0,
  "value": true
}
```

#### 写入寄存器
```
POST /api/write/register
Content-Type: application/json

{
  "slave_id": 1,
  "address": 0,
  "value": 1234
}
```

#### 获取历史记录
```
GET /api/history?limit=100
```

#### 获取统计信息
```
GET /api/stats
```

#### 健康检查
```
GET /health
```

### WebSocket API

连接到 `ws://localhost:8080/ws`

发送消息：
```json
{
  "type": "subscribe"
}
```

接收数据变化通知：
```json
{
  "type": "data_change",
  "slave_id": 1,
  "data_type": "coils",
  "address": 0
}
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t modbus-server .
```

### 运行容器

```bash
docker run -d \
  -p 5020:5020 \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/modbus_data.json:/app/modbus_data.json \
  --name modbus-server \
  modbus-server
```

### 使用 docker-compose

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 查看日志
docker-compose logs -f
```

## 🔧 故障排除

### RTU 串口权限问题

在 Linux 上，需要将用户添加到 `dialout` 组：

```bash
sudo usermod -a -G dialout $USER
```

然后重新登录。

### 端口被占用

如果端口 5020 或 8080 已被占用，可以在 `config.yaml` 中修改端口号。

### 依赖安装失败

确保使用的是 Python 3.8 或更高版本：

```bash
python --version
```

如果使用 Poetry，确保已安装最新版本：

```bash
pip install --upgrade poetry
```

## 📦 项目结构

```
modbus_slave_full/
├── modbus_slave_full/         # 主包
│   ├── __init__.py
│   ├── __main__.py            # 入口点
│   ├── config.py              # 配置管理
│   ├── datastore.py           # 数据存储
│   ├── protocol/              # 协议处理
│   │   ├── __init__.py
│   │   ├── handlers.py        # 功能码处理器
│   │   ├── tcp.py             # TCP 服务器
│   │   ├── rtu.py             # RTU 服务器
│   │   └── utils.py           # 工具函数
│   ├── web/                   # Web 控制台
│   │   ├── __init__.py
│   │   ├── server.py          # Web 服务器
│   │   ├── api.py             # API 路由
│   │   └── static/            # 前端资源
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── logger.py          # 日志管理
│       └── history.py         # 历史记录
├── tests/                     # 测试
│   ├── __init__.py
│   ├── test_protocol.py
│   ├── test_datastore.py
│   └── test_web.py
├── docs/                      # 文档
├── pyproject.toml             # Poetry 配置
├── config.example.yaml        # 配置示例
├── Dockerfile                 # Docker 文件
├── docker-compose.yml         # Docker Compose 配置
└── README.md                  # 本文件
```

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [pymodbus](https://github.com/pymodbus-dev/pymodbus) - Modbus 协议参考
- [aiohttp](https://github.com/aio-libs/aiohttp) - 异步 Web 框架
- [Poetry](https://python-poetry.org/) - Python 依赖管理

## 📞 联系方式

- 作者: clint
- Email: clinton_luO@163.com

## 🗺️ 路线图

- [ ] 支持更多功能码 (FC20, FC21)
- [ ] 添加 Prometheus metrics 导出
- [ ] 实现网关模式
- [ ] 添加数据模拟器
- [ ] 支持插件系统
- [ ] 添加更多数据可视化图表
- [ ] 支持多语言界面

## 📊 版本历史

### v1.0.0 (2025-12-24)

- ✨ 初始版本发布
- 🔌 支持 Modbus TCP/RTU
- 🌐 Web 控制台
- 💾 数据持久化
- 📊 历史记录和统计
- 🐳 Docker 支持
- 🧪 完整测试覆盖
