# 配置指南

## 配置文件

服务器使用 YAML 格式的配置文件。默认查找 `config.yaml`，可以通过命令行参数指定其他文件：

```bash
modbus-server --config /path/to/config.yaml
```

## 完整配置示例

```yaml
# Modbus 服务器配置

server:
  tcp:
    enabled: true           # 是否启用 TCP 服务器
    host: "0.0.0.0"        # 监听地址（0.0.0.0 表示所有接口）
    port: 5020             # TCP 端口
  
  rtu:
    enabled: false         # 是否启用 RTU 服务器
    port: "/dev/ttyUSB0"  # 串口设备
    baudrate: 9600        # 波特率
    bytesize: 8           # 数据位
    parity: "N"           # 校验位 (N=无, E=偶, O=奇)
    stopbits: 1           # 停止位
    timeout: 1.0          # 超时时间（秒）

slaves:
  - id: 1                        # 从站 ID
    name: "主设备"              # 从站名称
    coils: 100                   # 线圈数量 (FC01, FC05, FC15)
    discrete_inputs: 100         # 离散输入数量 (FC02)
    holding_registers: 100       # 保持寄存器数量 (FC03, FC06, FC16, FC23)
    input_registers: 100         # 输入寄存器数量 (FC04)
  
  - id: 2
    name: "从设备"
    coils: 50
    discrete_inputs: 50
    holding_registers: 50
    input_registers: 50

web:
  enabled: true           # 是否启用 Web 控制台
  host: "0.0.0.0"        # 监听地址
  port: 8080             # HTTP 端口
  auth:
    enabled: true        # 是否启用认证
    username: "admin"    # 用户名
    password: "admin123" # 密码（生产环境应使用哈希）

data:
  auto_save: true              # 是否自动保存
  save_interval: 60            # 保存间隔（秒）
  data_file: "modbus_data.json" # 数据文件路径
  history_enabled: true        # 是否启用历史记录
  history_max_size: 1000       # 历史记录最大数量

logging:
  level: "INFO"              # 日志级别 (DEBUG, INFO, WARNING, ERROR)
  file: "modbus_server.log"  # 日志文件路径
  max_size: 10485760         # 单个日志文件最大大小（字节，10MB）
  backup_count: 5            # 保留的日志文件备份数量
```

## 配置项详解

### Server 部分

#### TCP 配置

- `enabled`: 是否启用 TCP 服务器
- `host`: 监听地址
  - `"0.0.0.0"`: 监听所有网络接口
  - `"127.0.0.1"`: 仅本地访问
  - 具体 IP: 监听指定接口
- `port`: TCP 端口号（标准 Modbus TCP 端口是 502，但通常使用 5020 避免权限问题）

#### RTU 配置

- `enabled`: 是否启用 RTU 服务器
- `port`: 串口设备路径
  - Linux: `/dev/ttyUSB0`, `/dev/ttyS0` 等
  - Windows: `COM1`, `COM2` 等
  - macOS: `/dev/tty.usbserial-xxx`
- `baudrate`: 波特率（常用: 9600, 19200, 38400, 115200）
- `bytesize`: 数据位（7 或 8）
- `parity`: 校验位
  - `"N"`: 无校验
  - `"E"`: 偶校验
  - `"O"`: 奇校验
- `stopbits`: 停止位（1 或 2）
- `timeout`: 读取超时时间（秒）

### Slaves 部分

可以配置多个从站，每个从站有独立的数据区：

```yaml
slaves:
  - id: 1                  # 从站 ID (1-247)
    name: "描述性名称"
    coils: 100            # 线圈数量 (0-65535)
    discrete_inputs: 100  # 离散输入数量
    holding_registers: 100 # 保持寄存器数量
    input_registers: 100  # 输入寄存器数量
```

### Web 部分

- `enabled`: 是否启用 Web 控制台
- `host`: Web 服务器监听地址
- `port`: HTTP 端口
- `auth.enabled`: 是否启用认证
- `auth.username`: 登录用户名
- `auth.password`: 登录密码

**安全建议**: 生产环境应使用环境变量或密钥管理系统存储密码。

### Data 部分

- `auto_save`: 是否自动保存数据
- `save_interval`: 自动保存间隔（秒）
- `data_file`: 数据文件路径（JSON 格式）
- `history_enabled`: 是否记录历史
- `history_max_size`: 内存中保留的最大历史记录数

### Logging 部分

- `level`: 日志级别
  - `"DEBUG"`: 详细调试信息
  - `"INFO"`: 一般信息
  - `"WARNING"`: 警告信息
  - `"ERROR"`: 错误信息
- `file`: 日志文件路径（null 表示不写文件）
- `max_size`: 单个日志文件最大大小（字节）
- `backup_count`: 保留的旧日志文件数量

## 最佳实践

### 1. 生产环境配置

```yaml
server:
  tcp:
    host: "0.0.0.0"
    port: 502  # 需要 root 权限或使用 setcap

web:
  host: "127.0.0.1"  # 仅本地访问，通过反向代理暴露
  port: 8080
  auth:
    enabled: true

logging:
  level: "WARNING"  # 减少日志量
  file: "/var/log/modbus_server.log"
```

### 2. 开发环境配置

```yaml
server:
  tcp:
    host: "0.0.0.0"
    port: 5020

web:
  host: "0.0.0.0"
  port: 8080
  auth:
    enabled: false  # 方便开发

logging:
  level: "DEBUG"  # 详细日志
  file: "debug.log"
```

### 3. 测试环境配置

```yaml
server:
  tcp:
    host: "127.0.0.1"
    port: 15020  # 使用非标准端口

slaves:
  - id: 1
    name: "测试设备"
    coils: 10
    holding_registers: 10

data:
  auto_save: false  # 测试时不保存
  history_enabled: false
```

## 环境变量

某些配置可以通过环境变量覆盖：

```bash
# 设置 TCP 端口
export MODBUS_TCP_PORT=5020

# 设置 Web 端口
export MODBUS_WEB_PORT=8080

# 设置日志级别
export MODBUS_LOG_LEVEL=DEBUG
```

## 配置验证

启动服务器时，会自动验证配置。如果配置有误，会显示错误信息：

```bash
modbus-server --config config.yaml
```

## 动态重载配置

当前版本不支持动态重载配置。修改配置后需要重启服务器：

```bash
# 发送 SIGTERM 信号优雅停止
kill -TERM <pid>

# 或使用 Ctrl+C
```

## 下一步

- 查看 [API 文档](api.md)
- 阅读 [使用示例](examples.md)
