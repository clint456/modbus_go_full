# Modbus Go Library

[![Go Version](https://img.shields.io/badge/Go-1.18+-00ADD8?style=flat&logo=go)](https://go.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-94.4%25-brightgreen.svg)](DESIGN.md)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/clint456/modbus/releases)

纯 Go 实现的 Modbus 协议库，支持 RTU 和 TCP 两种模式。无需 RS485 ioctl 系统调用，可与 USB 转串口适配器无缝配合。

**生产就绪 | 测试通过率 94.4% | 完整文档**

## ✨ 核心特性

- 🚀 **双模式支持** - Modbus RTU 和 Modbus TCP
- 🔌 **USB 适配器友好** - 无需 RS485 ioctl，支持 CH340/CP2102/FTDI
- 🎯 **智能回显处理** - RTU 模式自动检测并处理硬件回显
- 🔄 **多字节序支持** - BigEndian/LittleEndian/BigEndianSwap/LittleEndianSwap
- 📊 **完整功能码** - 支持 12 个标准 Modbus 功能码
- 🧮 **多数据类型** - Uint16/Int16/Uint32/Int32/Float32
- 🛡️ **线程安全** - 支持并发使用
- ✅ **高测试覆盖** - 18 个测试用例，通过率 94.4%
- 📖 **完整文档** - 详细的设计文档和使用指南

## 📊 测试状态

| 模式 | 通过 | 总计 | 通过率 |
|------|------|------|--------|
| TCP  | 17   | 18   | 94.4%  |
| RTU  | 17   | 18   | 94.4%  |

查看 [完整测试报告](DESIGN.md#测试结果)

## 📦 安装

```bash
go get github.com/clint456/modbus
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
    "github.com/clint456/modbus"
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
    "github.com/clint456/modbus"
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

更多示例请查看 [example](example/) 目录。

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
| 0x14 | ReadFileRecord | 读取文件记录 | ⚠️ 需设备支持 |
| 0x15 | WriteFileRecord | 写入文件记录 | ⚠️ 需设备支持 |

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

查看 [example](example/) 目录获取完整示例：

- [tcp_example.go](example/tcp_example.go) - TCP 模式基础示例
- [rtu_example.go](example/rtu_example.go) - RTU 模式基础示例
- [comprehensive_example.go](example/comprehensive_example.go) - 综合测试程序

## 🧪 测试

运行综合测试程序：

```bash
cd example
go run comprehensive_example.go
```

## 🔌 硬件兼容性

已测试通过的设备：
- ✅ CH340/CH341 USB 转串口
- ✅ CP2102 USB 转串口
- ✅ FTDI FT232 USB 转串口
- ✅ 直接 RS485 适配器

## 📖 文档

- [DESIGN.md](DESIGN.md) - 完整设计文档
- [FILERECORD_TEST_GUIDE.md](FILERECORD_TEST_GUIDE.md) - FileRecord 功能测试指南

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

---

**版本**: 0.1.0  
**生产就绪** | **测试通过率 94.4%**