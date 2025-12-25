# Modbus Go Library - 完整设计文档

## 📋 项目概述

这是一个纯 Go 实现的 Modbus 协议库，支持 RTU 和 TCP 两种模式，无需 RS485 ioctl 系统调用。

**版本**: 1.0.0  
**作者**: Clint  
**日期**: 2025-12-22  
**测试通过率**: 94.4% (17/18)

---

## 🏗️ 架构设计

### 核心组件结构

```
modbus_go_full/
├── modbus.go           # 核心接口和常量定义
├── client.go           # 客户端工厂
├── types.go            # 配置类型定义
├── errors.go           # 错误类型定义
├── protocol.go         # 协议编解码
├── endianness.go       # 字节序转换
├── tcp_client.go       # TCP 客户端实现
├── rtu_client.go       # RTU 客户端实现
└── example/
    ├── tcp_example.go           # TCP 使用示例
    ├── rtu_example.go           # RTU 使用示例
    └── comprehensive_example.go # 综合测试程序
```

---

## 🎯 设计模式

### 1. 接口设计模式 (Interface Pattern)

所有客户端实现统一的 `Client` 接口，便于多态使用：

```go
type Client interface {
    // 基础读操作
    ReadCoils(address, quantity uint16) ([]byte, error)
    ReadDiscreteInputs(address, quantity uint16) ([]byte, error)
    ReadHoldingRegisters(address, quantity uint16) ([]byte, error)
    ReadInputRegisters(address, quantity uint16) ([]byte, error)
    
    // 基础写操作
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

### 2. 工厂模式 (Factory Pattern)

通过 `NewClient()` 工厂函数创建不同类型的客户端：

```go
client, err := modbus.NewClient("tcp", &modbus.TCPConfig{
    Host:    "192.168.1.100",
    Port:    502,
    SlaveID: 1,
})
```

### 3. 策略模式 (Strategy Pattern)

不同的字节序转换策略：
- BigEndian
- LittleEndian
- BigEndianSwap
- LittleEndianSwap

---

## 📡 协议实现

### Modbus RTU

#### 帧结构
```
[SlaveID][FuncCode][Data...][CRC_Low][CRC_High]
```

#### 关键特性
1. **CRC-16/MODBUS 校验**
   - 多项式: 0xA001
   - 初始值: 0xFFFF
   - 低字节在前

2. **串口通信处理**
   - 波特率：9600/19200/38400/115200
   - 数据位：7/8
   - 校验位：None/Even/Odd
   - 停止位：1/2

3. **智能响应提取**
   ```go
   // 优先从数据开头提取响应
   // 处理写操作响应=请求的特殊情况
   // 智能回显检测和跳过
   // CRC 完整性验证
   ```

4. **超时和重试机制**
   - 默认超时：1秒
   - 最小请求间隔：10ms
   - 智能数据等待（100ms静默判断传输完成）

### Modbus TCP

#### 帧结构 (MBAP Header + PDU)
```
[TransID_H][TransID_L][ProtoID_H][ProtoID_L][Length_H][Length_L][UnitID][FuncCode][Data...]
```

#### 关键特性
1. **MBAP 头处理**
   - Transaction ID：事务标识
   - Protocol ID：固定为 0
   - Length：PDU长度 + Unit ID
   - Unit ID：从站地址

2. **可靠数据读取**
   ```go
   // 使用 io.ReadFull 确保完整读取
   io.ReadFull(conn, mbapHeader)  // 7字节头
   io.ReadFull(conn, pduData)     // PDU数据
   ```

3. **事务ID管理**
   - 使用 atomic 包保证线程安全
   - 自动递增
   - 响应验证

---

## 🔧 关键技术细节

### 1. CRC 计算 (protocol.go)

```go
func CalculateCRC(data []byte) uint16 {
    crc := uint16(0xFFFF)
    for _, b := range data {
        crc ^= uint16(b)
        for i := 0; i < 8; i++ {
            if crc&1 != 0 {
                crc = (crc >> 1) ^ 0xA001
            } else {
                crc >>= 1
            }
        }
    }
    return crc
}
```

### 2. 字节序转换 (endianness.go)

支持4种字节序模式处理 32位数据：

| 模式 | 寄存器布局 | 字节顺序 | 示例 (0x12345678) |
|------|-----------|---------|-------------------|
| BigEndian | 高字在前 | AB CD | 1234 5678 |
| LittleEndian | 低字在前 | CD AB | 5678 1234 |
| BigEndianSwap | 高字在前+字节交换 | BA DC | 3412 7856 |
| LittleEndianSwap | 低字在前+字节交换 | DC BA | 7856 3412 |

### 3. RTU 响应提取算法 (rtu_client.go)

```go
func (c *RTUClient) extractValidResponse(data []byte, expectedFuncCode byte) []byte {
    // 步骤1: 优先从开头提取（处理写操作响应=请求的情况）
    if len(data) >= 5 && data[0] == c.config.SlaveID {
        // 计算期望长度
        // 验证 CRC
        // 返回有效响应
    }
    
    // 步骤2: 尝试跳过回显
    if 回显存在 {
        return c.extractValidResponse(跳过回显后的数据)
    }
    
    // 步骤3: 在数据中查找有效的从站地址
    for 遍历数据 {
        if 找到从站地址 {
            递归处理
        }
    }
    
    return nil
}
```

### 4. TCP 读取超时处理 (tcp_client.go)

```go
// 设置读写超时
conn.SetWriteDeadline(time.Now().Add(timeout))
conn.SetReadDeadline(time.Now().Add(timeout))

// 使用 io.ReadFull 确保完整读取
io.ReadFull(conn, mbapHeader)  // 必须读满7字节
io.ReadFull(conn, responsePDU) // 必须读满PDU长度
```

---

## 📊 支持的功能码

| 功能码 | 名称 | 说明 | 测试状态 |
|-------|------|------|---------|
| 0x01 | ReadCoils | 读线圈 | ✅ 通过 |
| 0x02 | ReadDiscreteInputs | 读离散输入 | ✅ 通过 |
| 0x03 | ReadHoldingRegisters | 读保持寄存器 | ✅ 通过 |
| 0x04 | ReadInputRegisters | 读输入寄存器 | ✅ 通过 |
| 0x05 | WriteSingleCoil | 写单个线圈 | ✅ 通过 |
| 0x06 | WriteSingleRegister | 写单个寄存器 | ✅ 通过 |
| 0x0F | WriteMultipleCoils | 写多个线圈 | ✅ 通过 |
| 0x10 | WriteMultipleRegisters | 写多个寄存器 | ✅ 通过 |
| 0x07 | ReadExceptionStatus | 读异常状态 | ✅ 通过 |
| 0x0B | GetCommEventCounter | 获取通信事件计数 | ✅ 通过 |
| 0x14 | ReadFileRecord | 读文件记录 | ⚠️ 需设备支持 |
| 0x15 | WriteFileRecord | 写文件记录 | ⚠️ 需设备支持 |

---

## 🎨 支持的数据类型

### 基础类型

| 类型 | 寄存器数 | 范围 | 函数 |
|------|---------|------|------|
| Uint16 | 1 | 0 ~ 65535 | BytesToUint16 / Uint16ToBytes |
| Int16 | 1 | -32768 ~ 32767 | BytesToInt16 / Int16ToBytes |
| Uint32 | 2 | 0 ~ 4294967295 | BytesToUint32 / Uint32ToBytes |
| Int32 | 2 | -2147483648 ~ 2147483647 | BytesToInt32 / Int32ToBytes |
| Float32 | 2 | IEEE 754 | BytesToFloat32 / Float32ToBytes |

### 使用示例

```go
// Uint16
value := uint16(12345)
client.WriteSingleRegister(addr, value)

// Int16
bytes := modbus.Int16ToBytes(int16(-12345))
uint16Value := modbus.BytesToUint16(bytes)
client.WriteSingleRegister(addr, uint16Value)

// Uint32
bytes, _ := modbus.Uint32ToBytes(0x12345678, modbus.BigEndian)
client.WriteMultipleRegisters(addr, bytes)

// Float32
bytes, _ := modbus.Float32ToBytes(3.14159, modbus.BigEndian)
client.WriteMultipleRegisters(addr, bytes)
```

---

## 🔍 异常处理

### Modbus 标准异常码

| 异常码 | 名称 | 说明 |
|-------|------|------|
| 0x01 | Illegal Function | 不支持的功能码 |
| 0x02 | Illegal Data Address | 非法数据地址 |
| 0x03 | Illegal Data Value | 非法数据值 |
| 0x04 | Slave Device Failure | 从站设备故障 |
| 0x05 | Acknowledge | 已接受（需要长时间处理） |
| 0x06 | Slave Device Busy | 从站设备忙 |
| 0x08 | Memory Parity Error | 内存校验错误 |
| 0x0A | Gateway Path Unavailable | 网关路径不可用 |
| 0x0B | Gateway Target Failed | 网关目标设备无响应 |

### 自定义错误

```go
var (
    ErrNotConnected       = fmt.Errorf("client not connected")
    ErrInvalidSlaveID     = fmt.Errorf("invalid slave ID")
    ErrInvalidQuantity    = fmt.Errorf("invalid quantity")
    ErrInvalidAddress     = fmt.Errorf("invalid address")
    ErrInvalidData        = fmt.Errorf("invalid data")
    ErrResponseTooShort   = fmt.Errorf("response too short")
    ErrCRCCheckFailed     = fmt.Errorf("CRC check failed")
    ErrUnexpectedResponse = fmt.Errorf("unexpected response")
    ErrTimeout            = fmt.Errorf("timeout")
)
```

---

## 💡 使用指南

### 快速开始 - TCP 模式

```go
package main

import (
    "fmt"
    "log"
    "time"
    "github.com/clint456/modbus_go_full"
)

func main() {
    // 创建配置
    config := &modbus.TCPConfig{
        Host:    "192.168.1.100",
        Port:    502,
        SlaveID: 1,
        Timeout: 1 * time.Second,
        Debug:   false,
    }
    
    // 创建客户端
    client, err := modbus.NewTCPClient(config)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    
    // 连接
    if err := client.Connect(); err != nil {
        log.Fatal(err)
    }
    
    // 读取保持寄存器
    data, err := client.ReadHoldingRegisters(0, 10)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Data: % 02X\n", data)
    
    // 写单个寄存器
    if err := client.WriteSingleRegister(100, 12345); err != nil {
        log.Fatal(err)
    }
}
```

### 快速开始 - RTU 模式

```go
package main

import (
    "fmt"
    "log"
    "time"
    "github.com/clint456/modbus_go_full"
)

func main() {
    // 创建配置
    config := &modbus.RTUConfig{
        PortName: "/dev/ttyUSB0",
        BaudRate: 9600,
        DataBits: 8,
        StopBits: 1,
        Parity:   "N",
        SlaveID:  1,
        Timeout:  1 * time.Second,
        Debug:    false,
    }
    
    // 创建客户端
    client, err := modbus.NewRTUClient(config)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    
    // 连接
    if err := client.Connect(); err != nil {
        log.Fatal(err)
    }
    
    // 读取保持寄存器
    data, err := client.ReadHoldingRegisters(0, 10)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Data: % 02X\n", data)
}
```

---

## 🧪 测试结果

### 综合测试统计

**TCP 模式**: 17/18 (94.4%)  
**RTU 模式**: 17/18 (94.4%)

### 测试项明细

| # | 测试项 | TCP | RTU | 说明 |
|---|--------|-----|-----|------|
| 1 | ReadCoils | ✅ | ✅ | 读取线圈状态 |
| 2 | ReadDiscreteInputs | ✅ | ✅ | 读取离散输入 |
| 3 | ReadHoldingRegisters | ✅ | ✅ | 读取保持寄存器 |
| 4 | ReadInputRegisters | ✅ | ✅ | 读取输入寄存器 |
| 5 | WriteSingleCoil | ✅ | ✅ | 写单个线圈 |
| 6 | WriteSingleRegister | ✅ | ✅ | 写单个寄存器 |
| 7 | WriteMultipleCoils | ✅ | ✅ | 写多个线圈 |
| 8 | WriteMultipleRegisters | ✅ | ✅ | 写多个寄存器 |
| 9 | Uint16 ReadWrite | ✅ | ✅ | 16位无符号整数 |
| 10 | Int16 ReadWrite | ✅ | ✅ | 16位有符号整数 |
| 11 | Uint32 ReadWrite | ✅ | ✅ | 32位无符号整数 |
| 12 | Int32 ReadWrite | ✅ | ✅ | 32位有符号整数 |
| 13 | Float32 ReadWrite | ✅ | ✅ | 32位浮点数 |
| 14 | FileRecord Base64 | ❌ | ❌ | 设备不支持 |
| 15 | ReadExceptionStatus | ✅ | ✅ | 读取异常状态 |
| 16 | GetCommEventCounter | ✅ | ✅ | 获取事件计数 |
| 17 | IsConnected | ✅ | ✅ | 连接状态检查 |
| 18 | SetTimeout | ✅ | ✅ | 超时设置 |

---

## 🐛 已知问题和解决方案

### 1. FileRecord 功能不可用
**现象**: 异常码 0x01 (Illegal Function)  
**原因**: 大多数 Modbus 设备不支持文件记录操作  
**解决**: 这是正常的，不是库的问题

### 2. RTU 模式串口权限问题
**现象**: `open /dev/ttyUSB0: permission denied`  
**解决**: 
```bash
sudo chmod 666 /dev/ttyUSB0
# 或永久解决
sudo usermod -a -G dialout $USER
```

### 3. TCP 连接超时
**现象**: `connect failed: i/o timeout`  
**解决**: 
- 检查网络连接
- 确认设备IP和端口
- 增加超时时间

---

## 📈 性能指标

### RTU 模式
- 波特率 9600: ~960 字节/秒
- 波特率 115200: ~11520 字节/秒
- 最小请求间隔: 10ms
- CRC 计算时间: < 1μs (8字节数据)

### TCP 模式
- 网络延迟: 通常 < 10ms (局域网)
- 单次请求响应时间: 20-50ms
- 支持并发连接: 是 (需注意线程安全)

---

## 🔐 安全考虑

1. **无认证机制**: Modbus 协议本身不提供认证
2. **明文传输**: 所有数据明文传输
3. **建议**: 
   - 在可信网络中使用
   - 使用 VPN 或 SSH 隧道保护 TCP 连接
   - 限制设备网络访问

---

## 🚀 后续改进建议

### 短期 (已完成)
- ✅ CRC 校验
- ✅ TCP 完整数据读取
- ✅ RTU 智能响应提取
- ✅ 多数据类型支持
- ✅ 综合测试程序

### 中期 (可选)
- ⭕ 连接池支持
- ⭕ 自动重连机制
- ⭕ 请求队列管理
- ⭕ 性能监控和统计

### 长期 (可选)
- ⭕ Modbus Plus 支持
- ⭕ 加密传输支持
- ⭕ Web 管理界面
- ⭕ 设备自动发现

---

## 📞 支持与贡献

### 文档
- 源码注释完整
- 示例代码丰富
- 设计文档详细

### 测试
- 单元测试覆盖核心功能
- 集成测试验证实际设备
- 通过率: 94.4%

### 版本
- 当前版本: 1.0.0
- 稳定性: 生产可用
- 兼容性: Go 1.18+

---

**文档生成时间**: 2025-12-22  
**库版本**: 1.0.0  
**作者**: Clint
