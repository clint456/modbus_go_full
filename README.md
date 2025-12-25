# Modbus Go Library

[![Go Version](https://img.shields.io/badge/Go-1.18+-00ADD8?style=flat&logo=go)](https://go.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](DESIGN.md)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/clint456/modbus_go_full/releases)

纯 Go 实现的 Modbus 协议库，支持 RTU 和 TCP 两种模式。无需 RS485 ioctl 系统调用，可与 USB 转串口适配器无缝配合。

**生产就绪 | 测试通过率 100% | 完整文档 | 配套工具**

## ✨ 核心特性

- 🚀 **双模式支持** - Modbus RTU 和 Modbus TCP
- 🔌 **USB 适配器友好** - 无需 RS485 ioctl，支持 CH340/CP2102/FTDI
- 🎯 **智能回显处理** - RTU 模式自动检测并处理硬件回显
- 🔄 **多字节序支持** - BigEndian/LittleEndian/BigEndianSwap/LittleEndianSwap
- 📊 **完整功能码** - 支持 12 个标准 Modbus 功能码
- 🧮 **多数据类型** - Uint16/Int16/Uint32/Int32/Float32
- 🛡️ **线程安全** - 支持并发使用
- ✅ **高测试覆盖** - 18 个测试用例，通过率 100%
- 🛠️ **配套工具** - Python Modbus 服务器，支持 Web 界面和 24 个功能码
- 📖 **完整文档** - 详细的设计文档和使用指南
![alt text](QQ20251224-093841.png) ![alt text](QQ20251224-093904.png)
## 📊 测试状态

| 模式 | 通过 | 总计 | 通过率 |
|------|------|------|--------|
| TCP  | 18   | 18   | 100%  |
| RTU  | 18   | 18   | 100%  |

**最新更新 (v0.2.0)**:
- ✅ 修复 Uint32 测试地址超范围问题 (202→72)
- ✅ 修复文件记录测试地址映射错误 (文件号1→0)
- ✅ 所有测试现已通过，支持 0-99 寄存器范围（可扩展至 65536）

查看 [完整测试报告](DESIGN.md#测试结果)

## 📦 安装

```bash
go get github.com/clint456/modbus_go_full
```

**依赖要求:**
- Go 1.18 或更高版本
- github.com/tarm/serial (RTU 模式)

## 🚀 快速开始

### TCP 模式

```go
package main

import (
    "fmt"
    "log"
    "time"
    "github.com/clint456/modbus_go_full"
)

func main() {
    // 创建 TCP 客户端
    config := &modbus.TCPConfig{
        Host:    "192.168.1.100",
        Port:    502,
        SlaveID: 1,
        Timeout: 1 * time.Second,
    }
    
    client, err := modbus.NewTCPClient(config)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    
    // 连接设备
    if err := client.Connect(); err != nil {
        log.Fatal(err)
    }
    
    // 读取保持寄存器
    data, err := client.ReadHoldingRegisters(0, 10)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("寄存器数据: % 02X\n", data)
    
    // 写单个寄存器
    if err := client.WriteSingleRegister(100, 12345); err != nil {
        log.Fatal(err)
    }
}
```

### RTU 模式

```go
package main

import (
    "fmt"
    "log"
    "time"
    "github.com/clint456/modbus_go_full"
)

func main() {
    // 创建 RTU 客户端
    config := &modbus.RTUConfig{
        PortName: "/dev/ttyUSB0",
        BaudRate: 9600,
        DataBits: 8,
        StopBits: 1,
        Parity:   "N",
        SlaveID:  1,
        Timeout:  1 * time.Second,
    }
    
    client, err := modbus.NewRTUClient(config)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    
    // 连接串口
    if err := client.Connect(); err != nil {
        log.Fatal(err)
    }
    
    // 读取保持寄存器
    data, err := client.ReadHoldingRegisters(0, 10)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("寄存器数据: % 02X\n", data)
}
```

更多示例请查看 [tools/modbus_poll_full](tools/modbus_poll_full/) 目录。

## 🛠️ 配套工具

### Modbus 测试服务器

本项目包含完整的 Python Modbus 服务器实现，适用于开发和测试：

**位置**: [tools/modbus_slave_full](tools/modbus_slave_full/)

**特性**:
- ✅ 支持 Modbus TCP 和 RTU 协议
- ✅ 支持 24 个标准功能码 (FC01-24)
- ✅ Web 控制台界面 (http://localhost:8080)
- ✅ 字符串读写操作支持
- ✅ 文件记录可视化
- ✅ 动态配置管理（寄存器大小可调整 0-65536）
- ✅ 实时数据监控和历史记录
- ✅ 数据持久化 (JSON)

**快速启动**:
```bash
cd tools/modbus_slave_full
poetry install
poetry run modbus-server

# 访问 Web 界面
# http://localhost:8080

# Modbus TCP 端口: 5020
```

**测试脚本**:
```bash
# 字符串操作测试
./test_string_operations.sh

# 文件记录测试
./test_file_records_practical.sh

# 配置管理测试
./test_config_management.sh

# 全功能码测试 (FC01-24)
python3 test_client.py
```

查看 [服务器文档](tools/modbus_slave_full/README.md) 了解更多信息。

### Go 客户端测试工具

**位置**: [tools/modbus_poll_full](tools/modbus_poll_full/)

**特性**:
- 综合测试程序，支持 18 个测试用例
- 自动化测试脚本
- 交互式测试模式

**使用方法**:
```bash
cd tools/modbus_poll_full
bash build.sh
./test_auto.sh  # 自动化测试
# 或
./comprehensive_example.o  # 交互式测试
```

## 📚 API 参考

### 客户端接口

```go
type Client interface {
    // 读取操作
    ReadCoils(address, quantity uint16) ([]byte, error)
    ReadDiscreteInputs(address, quantity uint16) ([]byte, error)
    ReadHoldingRegisters(address, quantity uint16) ([]byte, error)
    ReadInputRegisters(address, quantity uint16) ([]byte, error)
    
    // 写入操作
    WriteSingleCoil(address, value uint16) error
    WriteSingleRegister(address, value uint16) error
    WriteMultipleCoils(address uint16, values []bool) error
    WriteMultipleRegisters(address uint16, values []byte) error
    
    // 文件记录操作
    ReadFileRecord(fileNumber, recordNumber, recordLength uint16) ([]byte, error)
    WriteFileRecord(fileNumber, recordNumber uint16, data []byte) error
    
    // 诊断功能
    ReadExceptionStatus() (byte, error)
    GetCommEventCounter() (uint16, error)
    
    // 连接管理
    Connect() error
    Close() error
    IsConnected() bool
    
    // 配置
    SetTimeout(timeout time.Duration)
    SetSlaveID(slaveID byte)
}
```

### 支持的功能码

| 功能码 | 名称 | 描述 | 状态 |
|-------|------|------|------|
| 0x01 | ReadCoils | 读取线圈状态 (1-2000) | ✅ |
| 0x02 | ReadDiscreteInputs | 读取离散输入 (1-2000) | ✅ |
| 0x03 | ReadHoldingRegisters | 读取保持寄存器 (1-125) | ✅ |
| 0x04 | ReadInputRegisters | 读取输入寄存器 (1-125) | ✅ |
| 0x05 | WriteSingleCoil | 写单个线圈 | ✅ |
| 0x06 | WriteSingleRegister | 写单个寄存器 | ✅ |
| 0x0F | WriteMultipleCoils | 写多个线圈 | ✅ |
| 0x10 | WriteMultipleRegisters | 写多个寄存器 | ✅ |
| 0x07 | ReadExceptionStatus | 读取异常状态 | ✅ |
| 0x0B | GetCommEventCounter | 获取通信事件计数 | ✅ |
| 0x14 | ReadFileRecord | 读取文件记录 | ✅ 已修复 |
| 0x15 | WriteFileRecord | 写入文件记录 | ✅ 已修复 |

**注意**: 
- FileRecord 功能需要服务器支持，使用文件号 0 进行测试
- 服务器地址范围默认为 0-99，可动态扩展至 65536

### 支持的数据类型

本库提供了完整的数据类型转换函数：

```go
// Uint16 (单个寄存器)
value := uint16(12345)
client.WriteSingleRegister(addr, value)

// Int16 (单个寄存器)
bytes := modbus.Int16ToBytes(int16(-12345))
uint16Value := modbus.BytesToUint16(bytes)
client.WriteSingleRegister(addr, uint16Value)

// Uint32 (两个寄存器)
bytes, _ := modbus.Uint32ToBytes(0x12345678, modbus.BigEndian)
client.WriteMultipleRegisters(addr, bytes)

// Int32 (两个寄存器)
bytes, _ := modbus.Int32ToBytes(-123456, modbus.LittleEndian)
client.WriteMultipleRegisters(addr, bytes)

// Float32 (两个寄存器)
bytes, _ := modbus.Float32ToBytes(3.14159, modbus.BigEndian)
client.WriteMultipleRegisters(addr, bytes)
```

### 字节序支持

| 模式 | 说明 | 寄存器顺序 | 字节顺序 |
|------|------|-----------|---------|
| BigEndian | 高字在前 | AB CD | 1234 5678 |
| LittleEndian | 低字在前 | CD AB | 5678 1234 |
| BigEndianSwap | 高字在前+字节交换 | BA DC | 3412 7856 |
| LittleEndianSwap | 低字在前+字节交换 | DC BA | 7856 3412 |

## ⚙️ 配置选项

### RTU 配置

```go
type RTUConfig struct {
    PortName    string        // 串口名称，如 "/dev/ttyUSB0" 或 "COM1"
    BaudRate    int           // 波特率: 9600, 19200, 38400, 115200
    DataBits    int           // 数据位: 7 或 8
    StopBits    int           // 停止位: 1 或 2
    Parity      string        // 校验位: "N" (无), "E" (偶), "O" (奇)
    SlaveID     byte          // 从站地址: 1-247
    Timeout     time.Duration // 超时时间，默认 1s
    MinInterval time.Duration // 最小请求间隔，默认 10ms
    Debug       bool          // 启用调试日志
}
```

### TCP 配置

```go
type TCPConfig struct {
    Host    string        // 服务器地址，如 "192.168.1.100"
    Port    int           // 端口号，默认 502
    SlaveID byte          // 单元标识符: 0-255
    Timeout time.Duration // 超时时间，默认 1s
    Debug   bool          // 启用调试日志
}
```

## 🔧 错误处理

```go
data, err := client.ReadHoldingRegisters(0, 10)
if err != nil {
    // 检查是否为 Modbus 异常
    if modbusErr, ok := err.(*modbus.ModbusError); ok {
        fmt.Printf("Modbus 异常: %s\n", modbusErr.ExceptionString())
    } else {
        fmt.Printf("通信错误: %v\n", err)
    }
}
```

### Modbus 标准异常码

| 异常码 | 名称 | 说明 |
|-------|------|------|
| 0x01 | Illegal Function | 不支持的功能码 |
| 0x02 | Illegal Data Address | 非法数据地址 |
| 0x03 | Illegal Data Value | 非法数据值 |
| 0x04 | Slave Device Failure | 从站设备故障 |
| 0x05 | Acknowledge | 已接受（需要长时间处理） |
| 0x06 | Slave Device Busy | 从站设备忙 |

## 📝 更多示例

查看以下目录获取完整示例：

### Go 客户端示例
- [tools/modbus_poll_full/](tools/modbus_poll_full/) - Go 测试工具集
  - `tcp_example.go` - TCP 模式基础示例
  - `rtu_example.go` - RTU 模式基础示例
  - `comprehensive_example.go` - 综合测试程序（18 个测试用例）
  - `test_auto.sh` - 自动化测试脚本

### Python 服务器示例
- [tools/modbus_slave_full/](tools/modbus_slave_full/) - 完整的测试服务器
  - 支持 24 个 Modbus 功能码
  - Web 控制台界面
  - 字符串操作支持
  - 文件记录可视化
  - 配置管理功能

## 🧪 测试

### 自动化测试（推荐）

```bash
# 1. 启动测试服务器
cd tools/modbus_slave_full
poetry install
poetry run modbus-server &

# 2. 运行 Go 客户端自动化测试
cd tools/modbus_poll_full
bash build.sh
./test_auto.sh
```

### 交互式测试

```bash
cd tools/modbus_poll_full
go run comprehensive_example.go
```

### Python 服务器测试

```bash
cd tools/modbus_slave_full

# 字符串操作测试
./test_string_operations.sh

# 文件记录测试
./test_file_records_practical.sh

# 全功能码测试 (FC01-24)
python3 test_client.py
```

### Web 界面测试

1. 启动服务器: `poetry run modbus-server`
2. 打开浏览器: http://localhost:8080
3. 切换到 "📁 文件记录" 标签测试字符串和文件记录功能

## 🔌 硬件兼容性

已测试通过的设备：
- ✅ CH340/CH341 USB 转串口
- ✅ CP2102 USB 转串口
- ✅ FTDI FT232 USB 转串口
- ✅ 直接 RS485 适配器

## 📖 文档

- [DESIGN.md](DESIGN.md) - 完整设计文档和测试结果
- [FILERECORD_TEST_GUIDE.md](FILERECORD_TEST_GUIDE.md) - FileRecord 功能测试指南
- [tools/modbus_slave_full/README.md](tools/modbus_slave_full/README.md) - 测试服务器文档
- [tools/modbus_slave_full/STRING_OPERATIONS_GUIDE.md](tools/modbus_slave_full/STRING_OPERATIONS_GUIDE.md) - 字符串操作指南
- [tools/modbus_slave_full/FILE_RECORDS_GUIDE.md](tools/modbus_slave_full/FILE_RECORDS_GUIDE.md) - 文件记录功能指南
- [tools/modbus_slave_full/CONFIG_MANAGEMENT_GUIDE.md](tools/modbus_slave_full/CONFIG_MANAGEMENT_GUIDE.md) - 配置管理指南

## 🏗️ 项目结构

```
modbus_go_full/
├── client.go                    # 客户端工厂
├── tcp_client.go                # TCP 客户端实现
├── rtu_client.go                # RTU 客户端实现
├── protocol.go                  # 协议构建和解析
├── types.go                     # 数据类型转换
├── endianness.go                # 字节序处理
├── errors.go                    # 错误定义
├── modbus.go                    # 公共接口定义
├── go.mod                       # Go 模块定义
├── README.md                    # 本文档
├── DESIGN.md                    # 设计文档
└── tools/                       # 配套工具
    ├── modbus_poll_full/        # Go 客户端测试工具
    │   ├── comprehensive_example.go  # 综合测试程序
    │   ├── tcp_example.go       # TCP 示例
    │   ├── rtu_example.go       # RTU 示例
    │   ├── build.sh             # 编译脚本
    │   └── test_auto.sh         # 自动化测试
    └── modbus_slave_full/       # Python 测试服务器
        ├── modbus_slave_full/   # 服务器主包
        ├── tests/               # 单元测试
        ├── test_client.py       # 功能码测试客户端
        ├── test_string_operations.sh
        ├── test_file_records_practical.sh
        ├── pyproject.toml       # Poetry 配置
        └── README.md            # 服务器文档
```

## 🔐 安全考虑

⚠️ **重要提示:**
- Modbus 协议本身不提供认证机制
- 所有数据明文传输
- 建议在可信网络中使用
- 对于 TCP 模式，建议使用 VPN 或 SSH 隧道保护连接

## 🚀 性能指标

### RTU 模式
- 波特率 9600: ~960 字节/秒
- 波特率 115200: ~11520 字节/秒
- 最小请求间隔: 10ms
- CRC 计算时间: < 1μs (8字节数据)

### TCP 模式
- 网络延迟: < 10ms (局域网)
- 单次请求响应时间: 20-50ms
- 支持并发连接

## 📜 许可证

MIT License

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📞 支持

如有问题或建议，请提交 Issue。

## 🆕 更新日志

### v0.2.0 (2025-12-24)
- ✅ 修复 Uint32 测试地址超范围问题
- ✅ 修复文件记录测试地址映射错误
- ✅ 所有 18 个测试用例现已通过 (100%)
- 🆕 添加完整的 Python Modbus 测试服务器
- 🆕 Web 控制台界面，支持实时监控
- 🆕 字符串读写操作支持
- 🆕 文件记录可视化功能
- 🆕 动态配置管理（寄存器 0-65536）
- 🆕 支持 24 个 Modbus 功能码 (FC01-24)
- 📝 重组项目结构，tools/ 目录包含所有配套工具
- 📝 更新文档和测试脚本

### v0.1.0 (2025)
- 🎉 初始版本发布
- ✅ 支持 Modbus TCP 和 RTU
- ✅ 12 个标准功能码
- ✅ 多种数据类型和字节序支持

---

**版本**: 0.2.0  
**生产就绪** | **测试通过率 100%** | **配套工具齐全**