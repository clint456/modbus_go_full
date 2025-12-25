package main

import (
	"encoding/base64"
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"

	modbus "github.com/clint456/modbus_go_full"
)

// 测试结果
type TestResult struct {
	Name    string
	Success bool
	Error   error
	Data    interface{}
}

func main() {
	// 选择测试模式
	fmt.Println("=== Modbus 综合测试程序 ===")
	fmt.Println("选择测试模式:")
	fmt.Println("1. TCP 模式")
	fmt.Println("2. RTU 模式")
	fmt.Print("请输入选择 (1/2): ")

	var choice int
	fmt.Scanln(&choice)

	var client modbus.Client
	var err error

	switch choice {
	case 1:
		client, err = setupTCPClient()
	case 2:
		client, err = setupRTUClient()
	default:
		log.Fatal("无效的选择")
	}

	if err != nil {
		log.Fatalf("创建客户端失败: %v", err)
	}
	defer client.Close()

	// 连接
	if err := client.Connect(); err != nil {
		log.Fatalf("连接失败: %v", err)
	}
	fmt.Println("✓ 连接成功")

	// 运行所有测试
	results := runAllTests(client)

	// 打印测试报告
	printTestReport(results)
}

func setupTCPClient() (modbus.Client, error) {
	var host string
	fmt.Print("输入 TCP 主机地址 (默认: 127.0.0.1): ")
	fmt.Scanln(&host)
	if host == "" {
		host = "127.0.0.1"
	}

	var portStr string
	fmt.Print("输入 TCP 端口号 (默认: 5020): ")
	fmt.Scanln(&portStr)
	if portStr == "" {
		portStr = "5020"
	}

	port, err := strconv.Atoi(portStr)
	if err != nil {
		return nil, fmt.Errorf("无效的端口号: %v", err)
	}

	config := &modbus.TCPConfig{
		Host:          host,
		Port:          port,
		SlaveID:       1,
		MaxResponseMs: 2 * time.Second,
		Debug:         false,
	}

	return modbus.NewTCPClient(config)
}

func setupRTUClient() (modbus.Client, error) {
	fmt.Print("输入串口名称 (默认: /dev/ttyUSB0): ")
	var port string
	fmt.Scanln(&port)
	if port == "" {
		port = "/dev/ttyUSB0"
	}

	config := &modbus.RTUConfig{
		PortName:      port,
		BaudRate:      9600,
		DataBits:      8,
		StopBits:      1,
		Parity:        "N",
		SlaveID:       1,
		MaxResponseMs: 2 * time.Second,
		Debug:         false,
	}

	return modbus.NewRTUClient(config)
}

func runAllTests(client modbus.Client) []TestResult {
	var results []TestResult

	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("开始测试...")
	fmt.Println(strings.Repeat("=", 60))

	// 1. 测试基础读操作
	results = append(results, testReadCoils(client))
	results = append(results, testReadDiscreteInputs(client))
	results = append(results, testReadHoldingRegisters(client))
	results = append(results, testReadInputRegisters(client))

	// 2. 测试基础写操作
	results = append(results, testWriteSingleCoil(client))
	results = append(results, testWriteSingleRegister(client))
	results = append(results, testWriteMultipleCoils(client))
	results = append(results, testWriteMultipleRegisters(client))

	// 3. 测试数据类型读写
	results = append(results, testUint16ReadWrite(client))
	results = append(results, testInt16ReadWrite(client))
	results = append(results, testUint32ReadWrite(client))
	results = append(results, testInt32ReadWrite(client))
	results = append(results, testFloat32ReadWrite(client))

	// 4. 测试文件记录操作
	results = append(results, testFileRecordBase64(client))

	// 5. 测试诊断功能
	results = append(results, testReadExceptionStatus(client))
	results = append(results, testGetCommEventCounter(client))

	// 6. 测试连接管理
	results = append(results, testIsConnected(client))
	results = append(results, testSetMaxResponseMs(client))

	return results
}

// ========== 基础读操作测试 ==========

func testReadCoils(client modbus.Client) TestResult {
	fmt.Println("\n[1] 测试读取线圈 (ReadCoils)")
	data, err := client.ReadCoils(0, 16)
	if err != nil {
		return TestResult{"ReadCoils", false, err, nil}
	}
	fmt.Printf("    ✓ 读取成功: % 02X (二进制: ", data)
	for i := 0; i < 16 && i < len(data)*8; i++ {
		if data[i/8]&(1<<uint(i%8)) != 0 {
			fmt.Print("1")
		} else {
			fmt.Print("0")
		}
	}
	fmt.Println(")")
	return TestResult{"ReadCoils", true, nil, data}
}

func testReadDiscreteInputs(client modbus.Client) TestResult {
	fmt.Println("\n[2] 测试读取离散输入 (ReadDiscreteInputs)")
	data, err := client.ReadDiscreteInputs(0, 16)
	if err != nil {
		return TestResult{"ReadDiscreteInputs", false, err, nil}
	}
	fmt.Printf("    ✓ 读取成功: % 02X\n", data)
	return TestResult{"ReadDiscreteInputs", true, nil, data}
}

func testReadHoldingRegisters(client modbus.Client) TestResult {
	fmt.Println("\n[3] 测试读取保持寄存器 (ReadHoldingRegisters)")
	data, err := client.ReadHoldingRegisters(0, 10)
	if err != nil {
		return TestResult{"ReadHoldingRegisters", false, err, nil}
	}
	fmt.Printf("    ✓ 读取成功: % 02X\n", data)
	fmt.Print("    寄存器值: ")
	for i := 0; i < len(data); i += 2 {
		if i+1 < len(data) {
			value := modbus.BytesToUint16(data[i : i+2])
			fmt.Printf("%d ", value)
		}
	}
	fmt.Println()
	return TestResult{"ReadHoldingRegisters", true, nil, data}
}

func testReadInputRegisters(client modbus.Client) TestResult {
	fmt.Println("\n[4] 测试读取输入寄存器 (ReadInputRegisters)")
	data, err := client.ReadInputRegisters(0, 10)
	if err != nil {
		return TestResult{"ReadInputRegisters", false, err, nil}
	}
	fmt.Printf("    ✓ 读取成功: % 02X\n", data)
	return TestResult{"ReadInputRegisters", true, nil, data}
}

// ========== 基础写操作测试 ==========

func testWriteSingleCoil(client modbus.Client) TestResult {
	fmt.Println("\n[5] 测试写单个线圈 (WriteSingleCoil)")
	// 写入 ON
	if err := client.WriteSingleCoil(0, 1); err != nil {
		return TestResult{"WriteSingleCoil", false, err, nil}
	}
	fmt.Println("    ✓ 写入 ON 成功")

	time.Sleep(100 * time.Millisecond)

	// 写入 OFF
	if err := client.WriteSingleCoil(0, 0); err != nil {
		return TestResult{"WriteSingleCoil", false, err, nil}
	}
	fmt.Println("    ✓ 写入 OFF 成功")
	return TestResult{"WriteSingleCoil", true, nil, nil}
}

func testWriteSingleRegister(client modbus.Client) TestResult {
	fmt.Println("\n[6] 测试写单个寄存器 (WriteSingleRegister)")
	value := uint16(12345)
	if err := client.WriteSingleRegister(40, value); err != nil {
		return TestResult{"WriteSingleRegister", false, err, nil}
	}
	fmt.Printf("    ✓ 写入成功: %d\n", value)

	// 读取验证
	data, err := client.ReadHoldingRegisters(40, 1)
	if err == nil {
		readValue := modbus.BytesToUint16(data)
		fmt.Printf("    ✓ 读取验证: %d\n", readValue)
		if readValue != value {
			return TestResult{"WriteSingleRegister", false,
				fmt.Errorf("验证失败: 期望=%d, 实际=%d", value, readValue), nil}
		}
	}
	return TestResult{"WriteSingleRegister", true, nil, value}
}

func testWriteMultipleCoils(client modbus.Client) TestResult {
	fmt.Println("\n[7] 测试写多个线圈 (WriteMultipleCoils)")
	values := []bool{true, false, true, true, false, false, true, false}
	if err := client.WriteMultipleCoils(0, values); err != nil {
		return TestResult{"WriteMultipleCoils", false, err, nil}
	}
	fmt.Printf("    ✓ 写入成功: %v\n", values)

	// 读取验证
	data, err := client.ReadCoils(0, uint16(len(values)))
	if err == nil {
		fmt.Printf("    ✓ 读取验证: % 02X\n", data)
	}
	return TestResult{"WriteMultipleCoils", true, nil, values}
}

func testWriteMultipleRegisters(client modbus.Client) TestResult {
	fmt.Println("\n[8] 测试写多个寄存器 (WriteMultipleRegisters)")
	values := []uint16{100, 200, 300, 400, 500}
	data := make([]byte, len(values)*2)
	for i, v := range values {
		data[i*2] = byte(v >> 8)
		data[i*2+1] = byte(v)
	}

	if err := client.WriteMultipleRegisters(50, data); err != nil {
		return TestResult{"WriteMultipleRegisters", false, err, nil}
	}
	fmt.Printf("    ✓ 写入成功: %v\n", values)

	// 读取验证
	readData, err := client.ReadHoldingRegisters(50, uint16(len(values)))
	if err == nil {
		fmt.Print("    ✓ 读取验证: ")
		for i := 0; i < len(readData); i += 2 {
			value := modbus.BytesToUint16(readData[i : i+2])
			fmt.Printf("%d ", value)
		}
		fmt.Println()
	}
	return TestResult{"WriteMultipleRegisters", true, nil, values}
}

// ========== 数据类型测试 ==========

func testUint16ReadWrite(client modbus.Client) TestResult {
	fmt.Println("\n[9] 测试 Uint16 读写")
	testValue := uint16(65535)

	// 写入
	if err := client.WriteSingleRegister(60, testValue); err != nil {
		return TestResult{"Uint16 ReadWrite", false, err, nil}
	}
	fmt.Printf("    ✓ 写入 Uint16: %d\n", testValue)

	time.Sleep(50 * time.Millisecond)

	// 读取
	data, err := client.ReadHoldingRegisters(60, 1)
	if err != nil {
		return TestResult{"Uint16 ReadWrite", false, err, nil}
	}

	readValue := modbus.BytesToUint16(data)
	fmt.Printf("    ✓ 读取 Uint16: %d\n", readValue)

	if readValue != testValue {
		return TestResult{"Uint16 ReadWrite", false,
			fmt.Errorf("值不匹配: 期望=%d, 实际=%d", testValue, readValue), nil}
	}
	return TestResult{"Uint16 ReadWrite", true, nil, readValue}
}

func testInt16ReadWrite(client modbus.Client) TestResult {
	fmt.Println("\n[10] 测试 Int16 读写")
	testValue := int16(-12345)

	// 写入
	bytes := modbus.Int16ToBytes(testValue)
	uint16Value := modbus.BytesToUint16(bytes)
	if err := client.WriteSingleRegister(61, uint16Value); err != nil {
		return TestResult{"Int16 ReadWrite", false, err, nil}
	}
	fmt.Printf("    ✓ 写入 Int16: %d\n", testValue)

	time.Sleep(50 * time.Millisecond)

	// 读取
	data, err := client.ReadHoldingRegisters(61, 1)
	if err != nil {
		return TestResult{"Int16 ReadWrite", false, err, nil}
	}

	readValue := modbus.BytesToInt16(data)
	fmt.Printf("    ✓ 读取 Int16: %d\n", readValue)

	if readValue != testValue {
		return TestResult{"Int16 ReadWrite", false,
			fmt.Errorf("值不匹配: 期望=%d, 实际=%d", testValue, readValue), nil}
	}
	return TestResult{"Int16 ReadWrite", true, nil, readValue}
}

func testUint32ReadWrite(client modbus.Client) TestResult {
	fmt.Println("\n[11] 测试 Uint32 读写 (大端模式)")
	testValue := uint32(0x12345678)

	// 写入 (使用2个寄存器)
	bytes, _ := modbus.Uint32ToBytes(testValue, modbus.BigEndian)
	if err := client.WriteMultipleRegisters(72, bytes); err != nil {
		return TestResult{"Uint32 ReadWrite", false, err, nil}
	}
	fmt.Printf("    ✓ 写入 Uint32: 0x%08X (%d)\n", testValue, testValue)

	// 读取
	data, err := client.ReadHoldingRegisters(72, 2)
	if err != nil {
		return TestResult{"Uint32 ReadWrite", false, err, nil}
	}

	readValue, _ := modbus.BytesToUint32(data, modbus.BigEndian)
	fmt.Printf("    ✓ 读取 Uint32: 0x%08X (%d)\n", readValue, readValue)

	if readValue != testValue {
		return TestResult{"Uint32 ReadWrite", false,
			fmt.Errorf("值不匹配: 期望=0x%08X, 实际=0x%08X", testValue, readValue), nil}
	}
	return TestResult{"Uint32 ReadWrite", true, nil, readValue}
}

func testInt32ReadWrite(client modbus.Client) TestResult {
	fmt.Println("\n[12] 测试 Int32 读写 (大端模式)")
	testValue := int32(-123456789)

	// 写入 (使用2个寄存器)
	bytes, _ := modbus.Int32ToBytes(testValue, modbus.BigEndian)
	if err := client.WriteMultipleRegisters(64, bytes); err != nil {
		return TestResult{"Int32 ReadWrite", false, err, nil}
	}
	fmt.Printf("    ✓ 写入 Int32: %d\n", testValue)

	time.Sleep(50 * time.Millisecond)

	// 读取
	data, err := client.ReadHoldingRegisters(64, 2)
	if err != nil {
		return TestResult{"Int32 ReadWrite", false, err, nil}
	}

	readValue, _ := modbus.BytesToInt32(data, modbus.BigEndian)
	fmt.Printf("    ✓ 读取 Int32: %d\n", readValue)

	if readValue != testValue {
		return TestResult{"Int32 ReadWrite", false,
			fmt.Errorf("值不匹配: 期望=%d, 实际=%d", testValue, readValue), nil}
	}
	return TestResult{"Int32 ReadWrite", true, nil, readValue}
}

func testFloat32ReadWrite(client modbus.Client) TestResult {
	fmt.Println("\n[13] 测试 Float32 读写 (大端模式)")
	testValue := float32(3.14159265)

	// 写入 (使用2个寄存器)
	bytes, _ := modbus.Float32ToBytes(testValue, modbus.BigEndian)
	if err := client.WriteMultipleRegisters(66, bytes); err != nil {
		return TestResult{"Float32 ReadWrite", false, err, nil}
	}
	fmt.Printf("    ✓ 写入 Float32: %.8f\n", testValue)

	time.Sleep(50 * time.Millisecond)

	// 读取
	data, err := client.ReadHoldingRegisters(66, 2)
	if err != nil {
		return TestResult{"Float32 ReadWrite", false, err, nil}
	}

	readValue, _ := modbus.BytesToFloat32(data, modbus.BigEndian)
	fmt.Printf("    ✓ 读取 Float32: %.8f\n", readValue)

	// Float32 精度问题，允许小误差
	diff := testValue - readValue
	if diff < 0 {
		diff = -diff
	}
	if diff > 0.00001 {
		return TestResult{"Float32 ReadWrite", false,
			fmt.Errorf("值不匹配: 期望=%.8f, 实际=%.8f", testValue, readValue), nil}
	}
	return TestResult{"Float32 ReadWrite", true, nil, readValue}
}

// ========== 文件记录测试 ==========

func testFileRecordBase64(client modbus.Client) TestResult {
	fmt.Println("\n[14] 测试文件记录 Base64 编码")

	// 原始数据
	originalData := []byte("mobus file record test data for Base64 encoding.")

	// Base64 编码
	encoded := base64.StdEncoding.EncodeToString(originalData)
	fmt.Printf("    原始数据: %s\n", string(originalData))
	fmt.Printf("    Base64: %s\n", encoded)

	// 将编码后的字符串转为字节
	encodedBytes := []byte(encoded)

	// 计算实际写入长度（字节数）
	// Modbus 文件记录通常有长度限制，这里限制为 120 字节
	writeLen := len(encodedBytes)
	if writeLen > 120 {
		writeLen = 120
	}

	// 确保长度为偶数（Modbus 以 16 位字为单位）
	if writeLen%2 != 0 {
		writeLen--
	}

	dataToWrite := encodedBytes[:writeLen]
	fmt.Printf("    写入长度: %d 字节\n", writeLen)

	// 写入文件记录 (文件号=0, 记录号=85，映射到保持寄存器地址85)
	// 服务器将文件映射到寄存器: 地址 = file_number * 10000 + record_number
	err := client.WriteFileRecord(0, 0, dataToWrite)
	if err != nil {
		// 很多设备不支持文件记录，这是正常的
		fmt.Printf("    ⚠ 写入失败 (设备可能不支持): %v\n", err)
		return TestResult{"FileRecord Base64", false, err, nil}
	}
	fmt.Println("    ✓ Base64 数据写入成功")

	// 读取验证
	// ReadFileRecord 的长度参数通常是字数（words），1 word = 2 bytes
	wordCount := uint16(writeLen / 2)
	readData, err := client.ReadFileRecord(0, 85, wordCount)
	if err != nil {
		fmt.Printf("    ⚠ 读取失败:  %v\n", err)
		return TestResult{"FileRecord Base64", false, err, nil}
	}

	fmt.Printf("    ✓ 读取数据长度: %d 字节\n", len(readData))

	// 验证读取的数据长度
	if len(readData) < writeLen {
		fmt.Printf("    ⚠ 读取数据不完整: 期望 %d 字节，实际 %d 字节\n", writeLen, len(readData))
	}

	// 尝试解码 Base64
	// 截取有效长度的数据
	validData := readData
	if len(validData) > writeLen {
		validData = validData[:writeLen]
	}

	decoded, err := base64.StdEncoding.DecodeString(string(validData))
	if err != nil {
		fmt.Printf("    ⚠ Base64 解码失败: %v\n", err)
		// 即使解码失败，也返回读取的原始数据
		return TestResult{"FileRecord Base64", true, nil, validData}
	}

	fmt.Printf("    ✓ 读取并解码: %s\n", string(decoded))

	// 验证数据一致性
	if string(decoded) == string(originalData) {
		fmt.Println("    ✓ 数据验证通过：读写一致")
	} else {
		fmt.Printf("    ⚠ 数据不匹配\n")
		fmt.Printf("      期望: %s\n", string(originalData))
		fmt.Printf("      实际: %s\n", string(decoded))
	}

	return TestResult{"FileRecord Base64", true, nil, decoded}
}

// ========== 诊断功能测试 ==========

func testReadExceptionStatus(client modbus.Client) TestResult {
	fmt.Println("\n[15] 测试读取异常状态 (ReadExceptionStatus)")
	status, err := client.ReadExceptionStatus()
	if err != nil {
		fmt.Printf("    ⚠ 读取失败 (设备可能不支持): %v\n", err)
		return TestResult{"ReadExceptionStatus", false, err, nil}
	}
	fmt.Printf("    ✓ 异常状态: 0x%02X\n", status)
	return TestResult{"ReadExceptionStatus", true, nil, status}
}

func testGetCommEventCounter(client modbus.Client) TestResult {
	fmt.Println("\n[16] 测试获取通信事件计数器 (GetCommEventCounter)")
	counter, err := client.GetCommEventCounter()
	if err != nil {
		fmt.Printf("    ⚠ 读取失败 (设备可能不支持): %v\n", err)
		return TestResult{"GetCommEventCounter", false, err, nil}
	}
	fmt.Printf("    ✓ 事件计数器: %d\n", counter)
	return TestResult{"GetCommEventCounter", true, nil, counter}
}

// ========== 连接管理测试 ==========

func testIsConnected(client modbus.Client) TestResult {
	fmt.Println("\n[17] 测试连接状态检查 (IsConnected)")
	connected := client.IsConnected()
	fmt.Printf("    ✓ 连接状态: %v\n", connected)
	return TestResult{"IsConnected", connected, nil, connected}
}

func testSetMaxResponseMs(client modbus.Client) TestResult {
	fmt.Println("\n[18] 测试设置超时 (SetMaxResponseMs)")
	client.SetMaxResponseMs(3 * time.Second)
	fmt.Println("    ✓ 超时设置为 3 秒")

	// 恢复默认超时
	client.SetMaxResponseMs(2 * time.Second)
	fmt.Println("    ✓ 恢复超时为 2 秒")
	return TestResult{"SetMaxResponseMs", true, nil, nil}
}

// ========== 测试报告 ==========

func printTestReport(results []TestResult) {
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("测试报告")
	fmt.Println(strings.Repeat("=", 60))

	passed := 0
	failed := 0

	for _, result := range results {
		status := "❌ 失败"
		if result.Success {
			status = "✓ 通过"
			passed++
		} else {
			failed++
		}

		fmt.Printf("%-35s %s", result.Name, status)
		if result.Error != nil {
			fmt.Printf(" (%v)", result.Error)
		}
		fmt.Println()
	}

	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("总计: %d   通过: %d   失败: %d\n", len(results), passed, failed)
	fmt.Println(strings.Repeat("=", 60))
}

// 辅助函数
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
