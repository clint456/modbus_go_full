package modbus

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"sync"
	"time"

	"github.com/tarm/serial"
)

// RTUClient Modbus RTU 客户端
type RTUClient struct {
	config       *RTUConfig
	port         *serial.Port
	mutex        sync.Mutex
	lastRequest  []byte
	lastActivity time.Time
	connected    bool
}

// NewRTUClient 创建 RTU 客户端
func NewRTUClient(config *RTUConfig) (*RTUClient, error) {
	if config.MaxResponseMs == 0 {
		config.MaxResponseMs = 1000 * time.Millisecond
	}

	if config.MinInterval == 0 {
		config.MinInterval = 10 * time.Millisecond
	}

	client := &RTUClient{
		config: config,
	}

	return client, nil
}

// Connect 连接串口
func (c *RTUClient) Connect() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.connected && c.port != nil {
		return nil
	}

	var parity serial.Parity
	switch c.config.Parity {
	case "N", "None", "none":
		parity = serial.ParityNone
	case "E", "Even", "even":
		parity = serial.ParityEven
	case "O", "Odd", "odd":
		parity = serial.ParityOdd
	default:
		parity = serial.ParityNone
	}

	var stopBits serial.StopBits
	switch c.config.StopBits {
	case 1:
		stopBits = serial.Stop1
	case 2:
		stopBits = serial.Stop2
	default:
		stopBits = serial.Stop1
	}

	serialConfig := &serial.Config{
		Name:        c.config.PortName,
		Baud:        c.config.BaudRate,
		Size:        byte(c.config.DataBits),
		Parity:      parity,
		StopBits:    stopBits,
		ReadTimeout: c.config.MaxResponseMs,
	}

	port, err := serial.OpenPort(serialConfig)
	if err != nil {
		return fmt.Errorf("open port failed: %w", err)
	}

	c.port = port
	c.connected = true
	c.lastActivity = time.Now()

	if c.config.Debug {
		log.Printf("[Modbus RTU] Connected to %s at %d baud", c.config.PortName, c.config.BaudRate)
	}

	return nil
}

// Close 关闭连接
func (c *RTUClient) Close() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.port != nil {
		err := c.port.Close()
		c.port = nil
		c.connected = false

		if c.config.Debug {
			log.Printf("[Modbus RTU] Disconnected from %s", c.config.PortName)
		}

		return err
	}

	return nil
}

// IsConnected 检查连接状态
func (c *RTUClient) IsConnected() bool {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	return c.connected && c.port != nil
}

// SetMaxResponseMs 设置超时
func (c *RTUClient) SetMaxResponseMs(maxResponseMs time.Duration) {
	c.config.MaxResponseMs = maxResponseMs
}

// SetSlaveID 设置从站地址
func (c *RTUClient) SetSlaveID(slaveID byte) {
	c.config.SlaveID = slaveID
}

// transaction 执行事务
func (c *RTUClient) transaction(request []byte) ([]byte, error) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if !c.connected || c.port == nil {
		return nil, ErrNotConnected
	}

	// 确保最小间隔
	elapsed := time.Since(c.lastActivity)
	if elapsed < c.config.MinInterval {
		time.Sleep(c.config.MinInterval - elapsed)
	}

	c.lastRequest = request

	// 添加 CRC
	requestWithCRC := AppendCRC(request)

	if c.config.Debug {
		log.Printf("[Modbus RTU] TX: % 02X", requestWithCRC)
	}

	// 清空缓冲区
	if err := c.port.Flush(); err != nil {
		return nil, fmt.Errorf("flush failed: %w", err)
	}

	// 发送请求
	n, err := c.port.Write(requestWithCRC)
	if err != nil {
		return nil, fmt.Errorf("write failed: %w", err)
	}

	if n != len(requestWithCRC) {
		return nil, fmt.Errorf("incomplete write: %d/%d", n, len(requestWithCRC))
	}

	// 等待发送完成
	txTime := time.Duration(len(requestWithCRC)*11*1000000/c.config.BaudRate) * time.Microsecond
	time.Sleep(txTime + 2*time.Millisecond)

	// RS485回显处理：读取并丢弃发送的数据
	echoBuffer := make([]byte, len(requestWithCRC))
	echoDeadline := time.Now().Add(50 * time.Millisecond)
	totalEchoRead := 0
	for totalEchoRead < len(requestWithCRC) && time.Now().Before(echoDeadline) {
		n, err := c.port.Read(echoBuffer[totalEchoRead:])
		if n > 0 {
			totalEchoRead += n
			if c.config.Debug {
				log.Printf("[Modbus RTU] Echo discarded: % 02X (%d/%d bytes)",
					echoBuffer[:totalEchoRead], totalEchoRead, len(requestWithCRC))
			}
		}
		if err != nil && !isTimeout(err) && err != io.EOF {
			// 读取错误，但不影响继续（可能没有回显）
			break
		}
		if totalEchoRead >= len(requestWithCRC) {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}

	// 短暂延迟，等待实际响应开始到达
	time.Sleep(10 * time.Millisecond)

	// 读取响应
	response, err := c.readResponse(request[1])
	if err != nil {
		return nil, err
	}

	if c.config.Debug {
		log.Printf("[Modbus RTU] RX: % 02X", response)
	}

	// 验证 CRC
	if !VerifyCRC(response) {
		return nil, ErrCRCCheckFailed
	}

	c.lastActivity = time.Now()

	// 去掉 CRC 返回
	return response[:len(response)-2], nil
}

// readResponse 读取响应
func (c *RTUClient) readResponse(expectedFuncCode byte) ([]byte, error) {
	buffer := make([]byte, 512)
	totalRead := 0
	deadline := time.Now().Add(c.config.MaxResponseMs) // 最大响应超时时间
	lastReadTime := time.Now()

	for time.Now().Before(deadline) {
		// 小间隔读取
		n, err := c.port.Read(buffer[totalRead:])
		if n > 0 {
			totalRead += n
			lastReadTime = time.Now()
		}

		// 尝试提取有效响应
		if response := c.extractValidResponse(buffer[:totalRead], expectedFuncCode); response != nil {
			return response, nil
		}

		if err != nil && err != io.EOF && !isTimeout(err) {
			return nil, fmt.Errorf("read error: %w", err)
		}

		if totalRead > 256 {
			break
		}

		// 如果有数据但还不完整，等待更多数据到达
		if totalRead > 0 && time.Since(lastReadTime) < 100*time.Millisecond {
			time.Sleep(10 * time.Millisecond)
			continue
		}

		// 如果已经超过100ms没有新数据，认为传输完成
		if totalRead > 0 && time.Since(lastReadTime) >= 100*time.Millisecond {
			break
		}
	}

	if totalRead == 0 {
		return nil, ErrMaxResponseMsTimeOut
	}

	return nil, fmt.Errorf("invalid response (%d bytes): % 02X", totalRead, buffer[:totalRead])
}

// extractValidResponse 提取有效响应
func (c *RTUClient) extractValidResponse(data []byte, expectedFuncCode byte) []byte {
	// 首先尝试从开头提取响应
	if len(data) >= 5 {
		// 验证从站地址
		if data[0] == c.config.SlaveID {
			funcCode := data[1]

			// 计算期望长度
			var expectedLen int
			if funcCode&0x80 != 0 {
				expectedLen = 5
			} else {
				switch funcCode {
				case FuncCodeReadCoils, FuncCodeReadDiscreteInputs,
					FuncCodeReadHoldingRegisters, FuncCodeReadInputRegisters:
					if len(data) < 3 {
						return nil
					}
					byteCount := int(data[2])
					expectedLen = 3 + byteCount + 2

				case FuncCodeWriteSingleCoil, FuncCodeWriteSingleRegister,
					FuncCodeWriteMultipleCoils, FuncCodeWriteMultipleRegisters:
					expectedLen = 8

				case FuncCodeReadFileRecord:
					if len(data) < 3 {
						return nil
					}
					respLength := int(data[2])
					expectedLen = 3 + respLength + 2

				case FuncCodeWriteFileRecord:
					if len(data) < 3 {
						return nil
					}
					dataLength := int(data[2])
					expectedLen = 3 + dataLength + 2

				case FuncCodeReadExceptionStatus:
					expectedLen = 5

				case FuncCodeGetCommEventCounter:
					expectedLen = 8

				default:
					return nil
				}
			}

			if len(data) >= expectedLen {
				// 验证CRC
				fullResponse := data[:expectedLen]
				if VerifyCRC(fullResponse) {
					return fullResponse
				}
			}
		}
	}

	// 如果从开头提取失败，尝试跳过可能的回显
	if len(data) >= len(c.lastRequest)+2+5 { // 请求+CRC+至少5字节响应
		requestWithCRC := AppendCRC(c.lastRequest)
		if bytes.HasPrefix(data, requestWithCRC) {
			// 递归处理跳过回显后的数据
			return c.extractValidResponse(data[len(requestWithCRC):], expectedFuncCode)
		}
	}

	// 如果都失败，尝试在数据中查找有效的从站地址
	for i := 1; i < len(data)-5; i++ {
		if data[i] == c.config.SlaveID {
			return c.extractValidResponse(data[i:], expectedFuncCode)
		}
	}

	return nil
}

// 实现 Client 接口的方法
func (c *RTUClient) ReadCoils(address, quantity uint16) ([]byte, error) {
	request := BuildReadRequest(c.config.SlaveID, FuncCodeReadCoils, address, quantity)
	response, err := c.transaction(request)
	if err != nil {
		return nil, err
	}
	return ParseResponse(response, FuncCodeReadCoils)
}

func (c *RTUClient) ReadDiscreteInputs(address, quantity uint16) ([]byte, error) {
	request := BuildReadRequest(c.config.SlaveID, FuncCodeReadDiscreteInputs, address, quantity)
	response, err := c.transaction(request)
	if err != nil {
		return nil, err
	}
	return ParseResponse(response, FuncCodeReadDiscreteInputs)
}

func (c *RTUClient) ReadHoldingRegisters(address, quantity uint16) ([]byte, error) {
	request := BuildReadRequest(c.config.SlaveID, FuncCodeReadHoldingRegisters, address, quantity)
	response, err := c.transaction(request)
	if err != nil {
		return nil, err
	}
	return ParseResponse(response, FuncCodeReadHoldingRegisters)
}

func (c *RTUClient) ReadInputRegisters(address, quantity uint16) ([]byte, error) {
	request := BuildReadRequest(c.config.SlaveID, FuncCodeReadInputRegisters, address, quantity)
	response, err := c.transaction(request)
	if err != nil {
		return nil, err
	}
	return ParseResponse(response, FuncCodeReadInputRegisters)
}

func (c *RTUClient) WriteSingleCoil(address, value uint16) error {
	if value != 0 {
		value = 0xFF00
	}
	request := BuildWriteSingleRequest(c.config.SlaveID, FuncCodeWriteSingleCoil, address, value)
	response, err := c.transaction(request)
	if err != nil {
		return err
	}
	_, err = ParseResponse(response, FuncCodeWriteSingleCoil)
	return err
}

func (c *RTUClient) WriteSingleRegister(address, value uint16) error {
	request := BuildWriteSingleRequest(c.config.SlaveID, FuncCodeWriteSingleRegister, address, value)
	response, err := c.transaction(request)
	if err != nil {
		return err
	}
	_, err = ParseResponse(response, FuncCodeWriteSingleRegister)
	return err
}

func (c *RTUClient) WriteMultipleCoils(address uint16, values []bool) error {
	request := BuildWriteMultipleCoilsRequest(c.config.SlaveID, address, values)
	response, err := c.transaction(request)
	if err != nil {
		return err
	}
	_, err = ParseResponse(response, FuncCodeWriteMultipleCoils)
	return err
}

func (c *RTUClient) WriteMultipleRegisters(address uint16, values []byte) error {
	request := BuildWriteMultipleRegistersRequest(c.config.SlaveID, address, values)
	response, err := c.transaction(request)
	if err != nil {
		return err
	}
	_, err = ParseResponse(response, FuncCodeWriteMultipleRegisters)
	return err
}

func (c *RTUClient) ReadFileRecord(fileNumber, recordNumber, recordLength uint16) ([]byte, error) {
	request := BuildReadFileRecordRequest(c.config.SlaveID, fileNumber, recordNumber, recordLength)
	response, err := c.transaction(request)
	if err != nil {
		return nil, err
	}
	return ParseResponse(response, FuncCodeReadFileRecord)
}

func (c *RTUClient) WriteFileRecord(fileNumber, recordNumber uint16, data []byte) error {
	request := BuildWriteFileRecordRequest(c.config.SlaveID, fileNumber, recordNumber, data)
	response, err := c.transaction(request)
	if err != nil {
		return err
	}
	_, err = ParseResponse(response, FuncCodeWriteFileRecord)
	return err
}

func (c *RTUClient) ReadExceptionStatus() (byte, error) {
	request := []byte{c.config.SlaveID, FuncCodeReadExceptionStatus}
	response, err := c.transaction(request)
	if err != nil {
		return 0, err
	}
	data, err := ParseResponse(response, FuncCodeReadExceptionStatus)
	if err != nil {
		return 0, err
	}
	if len(data) < 1 {
		return 0, ErrResponseTooShort
	}
	return data[0], nil
}

func (c *RTUClient) GetCommEventCounter() (uint16, error) {
	request := []byte{c.config.SlaveID, FuncCodeGetCommEventCounter}
	response, err := c.transaction(request)
	if err != nil {
		return 0, err
	}
	data, err := ParseResponse(response, FuncCodeGetCommEventCounter)
	if err != nil {
		return 0, err
	}
	if len(data) < 4 {
		return 0, ErrResponseTooShort
	}
	return BytesToUint16(data[2:4]), nil
}

func isTimeout(err error) bool {
	return err == io.EOF || bytes.Contains([]byte(err.Error()), []byte("timeout"))
}
