# FileRecord 功能测试指南

## 📖 功能概述

Modbus 文件记录功能（功能码 0x14 和 0x15）是 Modbus 协议的**可选高级功能**，用于读写设备内部的文件系统或结构化数据存储。

## ⚠️ 重要说明

**大多数标准 Modbus 设备不支持文件记录功能**。这是正常的，因为：
1. 简单的 I/O 设备通常只需要寄存器和线圈
2. 文件记录增加了设备复杂度和成本
3. 不是 Modbus 核心功能

## 🎯 支持文件记录的设备类型

以下类型的设备**可能**支持文件记录：

### 1. 高端 PLC
- Schneider Electric Modicon 系列
- Siemens S7 系列（通过特定配置）
- Allen-Bradley ControlLogix

### 2. 专用数据采集器
- 支持数据记录的 RTU
- 历史数据存储设备
- 带存储功能的网关

### 3. Modbus 模拟器/测试工具
- **Modbus Slave** (Modbus Tools)
- **ModRSsim2** (支持文件记录配置)
- **pymodbus** 服务器模式

## 🛠️ 测试准备

### 方案1: 使用 Modbus 模拟器

#### 步骤1: 安装 pymodbus

```bash
pip install pymodbus
```

#### 步骤2: 创建支持文件记录的服务器

创建文件 `modbus_server_with_files.py`:

```python
#!/usr/bin/env python3
"""
Modbus 服务器 - 支持文件记录功能
"""
from pymodbus.server import StartTcpServer, StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer, ModbusSocketFramer
import logging

# 配置日志
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# 创建数据存储
# hr = 保持寄存器, ir = 输入寄存器, co = 线圈, di = 离散输入
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)

# 自定义支持文件记录的上下文
class FileRecordDataStore:
    """文件记录数据存储"""
    def __init__(self):
        # 模拟文件存储：file_number -> {record_number -> data}
        self.files = {}
        # 初始化一些测试文件
        self.files[1] = {}  # 文件1
        self.files[2] = {}  # 文件2
    
    def read_file_record(self, file_number, record_number, record_length):
        """读取文件记录"""
        if file_number not in self.files:
            return None
        if record_number not in self.files[file_number]:
            # 返回空数据
            return b'\x00' * (record_length * 2)
        return self.files[file_number][record_number]
    
    def write_file_record(self, file_number, record_number, data):
        """写入文件记录"""
        if file_number not in self.files:
            self.files[file_number] = {}
        self.files[file_number][record_number] = data
        print(f"✓ 写入文件 {file_number}, 记录 {record_number}: {data.hex()}")
        return True

# 创建文件存储实例
file_store = FileRecordDataStore()

# 自定义上下文处理器
class CustomModbusSlaveContext(ModbusSlaveContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_store = file_store

context = ModbusServerContext(slaves={
    1: CustomModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=ModbusSequentialDataBlock(0, [0]*100),
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
}, single=False)

# 启动 TCP 服务器
print("=" * 60)
print("Modbus TCP 服务器启动 - 支持文件记录")
print("地址: 0.0.0.0:502")
print("从站ID: 1")
print("=" * 60)
print("支持的功能:")
print("  - 标准读写操作 (0x01-0x10)")
print("  - 文件记录读取 (0x14)")
print("  - 文件记录写入 (0x15)")
print("=" * 60)

StartTcpServer(
    context=context,
    address=("0.0.0.0", 502),
    framer=ModbusSocketFramer
)
```

#### 步骤3: 启动服务器

```bash
python3 modbus_server_with_files.py
```

### 方案2: 使用真实设备

如果你有支持文件记录的真实设备：

1. **查看设备文档**
   - 确认支持功能码 0x14 和 0x15
   - 查找文件编号范围
   - 查找记录编号范围
   - 了解记录长度限制

2. **常见配置位置**
   - PLC 配置软件中的"文件系统"或"数据块"设置
   - 设备用户手册中的"高级功能"章节
   - Modbus 映射表中的文件区域定义

## 🧪 测试步骤

### 测试1: 基础写入和读取

创建测试程序 `test_file_record.go`:

```go
package main

import (
    "encoding/base64"
    "fmt"
    "log"
    "time"
    "github.com/clint456/modbus_go_full"
)

func main() {
    // 连接到支持文件记录的设备/模拟器
    config := &modbus.TCPConfig{
        Host:    "127.0.0.1",  // 本地模拟器
        Port:    502,
        SlaveID: 1,
        MaxResponseMs: 2 * time.Second,
        Debug:   true,
    }
    
    client, err := modbus.NewTCPClient(config)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    
    if err := client.Connect(); err != nil {
        log.Fatal(err)
    }
    
    fmt.Println("✓ 连接成功")
    fmt.Println()
    
    // 测试1: 写入简单数据
    fmt.Println("=== 测试1: 写入简单数据 ===")
    testData := []byte{0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0}
    err = client.WriteFileRecord(1, 0, testData)
    if err != nil {
        log.Printf("❌ 写入失败: %v", err)
    } else {
        fmt.Printf("✓ 写入成功: % 02X\n", testData)
    }
    fmt.Println()
    
    // 等待数据稳定
    time.Sleep(100 * time.Millisecond)
    
    // 测试2: 读取数据
    fmt.Println("=== 测试2: 读取数据 ===")
    readData, err := client.ReadFileRecord(1, 0, uint16(len(testData)/2))
    if err != nil {
        log.Printf("❌ 读取失败: %v", err)
    } else {
        fmt.Printf("✓ 读取成功: % 02X\n", readData)
        
        // 验证数据
        if len(readData) >= len(testData) {
            match := true
            for i := 0; i < len(testData); i++ {
                if readData[i] != testData[i] {
                    match = false
                    break
                }
            }
            if match {
                fmt.Println("✓ 数据验证通过")
            } else {
                fmt.Println("❌ 数据不匹配")
            }
        }
    }
    fmt.Println()
    
    // 测试3: Base64 编码数据
    fmt.Println("=== 测试3: Base64 编码数据 ===")
    originalText := "Hello Modbus FileRecord!"
    encoded := base64.StdEncoding.EncodeToString([]byte(originalText))
    fmt.Printf("原始文本: %s\n", originalText)
    fmt.Printf("Base64: %s\n", encoded)
    
    encodedBytes := []byte(encoded)
    // 确保长度是偶数（Modbus 寄存器是16位）
    if len(encodedBytes)%2 != 0 {
        encodedBytes = append(encodedBytes, 0)
    }
    
    err = client.WriteFileRecord(2, 0, encodedBytes)
    if err != nil {
        log.Printf("❌ 写入Base64失败: %v", err)
    } else {
        fmt.Println("✓ Base64数据写入成功")
        
        time.Sleep(100 * time.Millisecond)
        
        // 读取并解码
        readData, err := client.ReadFileRecord(2, 0, uint16(len(encodedBytes)/2))
        if err != nil {
            log.Printf("❌ 读取失败: %v", err)
        } else {
            fmt.Printf("✓ 读取Base64数据: %s\n", string(readData[:len(encoded)]))
            
            decoded, err := base64.StdEncoding.DecodeString(string(readData[:len(encoded)]))
            if err == nil {
                fmt.Printf("✓ 解码成功: %s\n", string(decoded))
            }
        }
    }
}
```

### 测试2: 大数据块测试

```go
// 测试写入大数据块（最大120字节）
func testLargeData(client modbus.Client) {
    fmt.Println("=== 测试大数据块 ===")
    
    // 创建120字节测试数据
    largeData := make([]byte, 120)
    for i := range largeData {
        largeData[i] = byte(i)
    }
    
    // 分块写入（每次60字节）
    for i := 0; i < len(largeData); i += 60 {
        end := i + 60
        if end > len(largeData) {
            end = len(largeData)
        }
        
        chunk := largeData[i:end]
        recordNum := uint16(i / 60)
        
        err := client.WriteFileRecord(3, recordNum, chunk)
        if err != nil {
            log.Printf("❌ 写入块 %d 失败: %v", recordNum, err)
            return
        }
        fmt.Printf("✓ 写入块 %d: %d 字节\n", recordNum, len(chunk))
    }
    
    // 读取验证
    for i := 0; i < len(largeData); i += 60 {
        end := i + 60
        if end > len(largeData) {
            end = len(largeData)
        }
        
        recordNum := uint16(i / 60)
        expectedLen := uint16((end - i) / 2)
        
        data, err := client.ReadFileRecord(3, recordNum, expectedLen)
        if err != nil {
            log.Printf("❌ 读取块 %d 失败: %v", recordNum, err)
            return
        }
        fmt.Printf("✓ 读取块 %d: %d 字节\n", recordNum, len(data))
    }
}
```

## 📋 测试检查清单

运行测试时检查以下项目：

- [ ] 设备/模拟器支持功能码 0x14 (ReadFileRecord)
- [ ] 设备/模拟器支持功能码 0x15 (WriteFileRecord)
- [ ] 写入操作返回成功
- [ ] 读取操作可以取回写入的数据
- [ ] Base64 编码/解码正确
- [ ] 大数据块分块读写正常
- [ ] 多个文件编号可以独立操作
- [ ] 错误处理正确（如非法文件号、记录号）

## 🔍 故障排查

### 问题1: 异常码 0x01 (Illegal Function)
**原因**: 设备不支持文件记录  
**解决**: 使用支持的模拟器或设备

### 问题2: 异常码 0x02 (Illegal Data Address)
**原因**: 文件号或记录号超出范围  
**解决**: 查看设备文档，使用有效的文件号和记录号

### 问题3: 异常码 0x03 (Illegal Data Value)
**原因**: 数据长度不正确  
**解决**: 
- 确保数据长度是偶数（16位寄存器）
- 不超过设备的最大记录长度（通常120字节）

### 问题4: 读取的数据为全零
**原因**: 记录未初始化或文件号不存在  
**解决**: 先写入数据再读取

## 📊 预期测试结果

成功的测试输出应该类似：

```
✓ 连接成功

=== 测试1: 写入简单数据 ===
✓ 写入成功: 12 34 56 78 9A BC DE F0

=== 测试2: 读取数据 ===
✓ 读取成功: 12 34 56 78 9A BC DE F0
✓ 数据验证通过

=== 测试3: Base64 编码数据 ===
原始文本: Hello Modbus FileRecord!
Base64: SGVsbG8gTW9kYnVzIEZpbGVSZWNvcmQh
✓ Base64数据写入成功
✓ 读取Base64数据: SGVsbG8gTW9kYnVzIEZpbGVSZWNvcmQh
✓ 解码成功: Hello Modbus FileRecord!
```

## 🎓 进阶测试

1. **并发测试**: 多个客户端同时读写不同文件
2. **边界测试**: 测试最大记录长度
3. **错误恢复**: 测试异常情况下的恢复
4. **性能测试**: 测量读写速度
5. **持久性测试**: 断电重启后数据是否保留

## 📚 参考资料

- Modbus Application Protocol V1.1b3
- Modbus 功能码详解
- pymodbus 文档: https://pymodbus.readthedocs.io/
- Modbus 文件记录规范

---

**最后更新**: 2025-12-22  
**作者**: Clint
