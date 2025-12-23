# 安装指南

## 系统要求

- Python 3.8 或更高版本
- Poetry 1.2+ (推荐) 或 pip
- 可选: Docker 和 Docker Compose

## 方法 1: 使用 Poetry (推荐)

### 1. 安装 Poetry

如果还未安装 Poetry，请先安装：

```bash
# Linux, macOS, WSL
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd modbus-slave-full
```

### 3. 安装依赖

```bash
# 安装生产依赖
poetry install --no-dev

# 或安装包括开发依赖
poetry install
```

### 4. 运行服务器

```bash
# 方式 1: 使用 Poetry 命令
poetry run modbus-server

# 方式 2: 激活虚拟环境后运行
poetry shell
modbus-server
```

## 方法 2: 使用 pip

### 1. 创建虚拟环境 (推荐)

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install aiohttp pyserial-asyncio pyyaml aiohttp-cors
```

### 3. 运行服务器

```bash
python -m modbus_slave_full
```

## 方法 3: 使用 Docker

### 前置要求

- Docker 20.10+
- Docker Compose 1.29+

### 使用 Docker Compose (推荐)

```bash
# 1. 创建配置文件
cp config.example.yaml config.yaml

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t modbus-server .

# 2. 运行容器
docker run -d \
  -p 5020:5020 \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/modbus_data.json:/app/modbus_data.json \
  --name modbus-server \
  modbus-server

# 3. 查看日志
docker logs -f modbus-server

# 4. 停止容器
docker stop modbus-server
docker rm modbus-server
```

## 配置串口 (RTU 模式)

### Linux

```bash
# 添加用户到 dialout 组
sudo usermod -a -G dialout $USER

# 重新登录或使用
newgrp dialout

# 检查串口设备
ls -l /dev/ttyUSB*
ls -l /dev/ttyS*
```

### Windows

在 Windows 上，串口通常命名为 `COM1`, `COM2` 等。在配置文件中使用：

```yaml
server:
  rtu:
    port: "COM3"
```

### macOS

```bash
# 查看串口设备
ls -l /dev/tty.*
```

在配置文件中使用：

```yaml
server:
  rtu:
    port: "/dev/tty.usbserial-xxx"
```

## 验证安装

### 1. 检查服务器状态

启动服务器后，应该看到类似输出：

```
2025-12-24 10:00:00 - modbus_slave_full.__main__ - INFO - 日志系统初始化完成，级别: INFO
2025-12-24 10:00:00 - modbus_slave_full.datastore - INFO - 初始化从站 1: 100 线圈, 100 寄存器
2025-12-24 10:00:00 - modbus_slave_full.protocol.tcp - INFO - Modbus TCP 服务器启动: 0.0.0.0:5020
2025-12-24 10:00:00 - modbus_slave_full.web.server - INFO - Web 服务器启动: http://0.0.0.0:8080
2025-12-24 10:00:00 - modbus_slave_full.__main__ - INFO - Modbus 服务器启动完成
```

### 2. 测试 Web 控制台

在浏览器中访问: `http://localhost:8080`

### 3. 测试 Modbus TCP

使用 Modbus 客户端工具（如 QModMaster, pymodbus）连接到 `localhost:5020`。

### 4. 测试 API

```bash
# 获取从站列表
curl http://localhost:8080/api/slaves

# 获取数据
curl http://localhost:8080/api/data?slave_id=1

# 健康检查
curl http://localhost:8080/health
```

## 常见问题

### Q: Poetry install 失败

A: 确保使用的是 Python 3.8+，更新 Poetry：

```bash
poetry self update
```

### Q: 端口被占用

A: 修改 `config.yaml` 中的端口号，或停止占用端口的程序：

```bash
# Linux/macOS
lsof -i :5020
lsof -i :8080

# Windows
netstat -ano | findstr :5020
netstat -ano | findstr :8080
```

### Q: 串口权限被拒绝

A: 参考上面的"配置串口"部分。

### Q: 导入错误

A: 确保已激活虚拟环境，或使用 `poetry run` 前缀。

## 下一步

- 阅读 [配置指南](configuration.md)
- 查看 [API 文档](api.md)
- 浏览 [使用示例](examples.md)
