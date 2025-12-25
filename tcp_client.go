package modbus

import (
	"fmt"
	"io"
	"log"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

// TCPClient Modbus TCP 客户端
type TCPClient struct {
	config        *TCPConfig
	conn          net.Conn
	mutex         sync.Mutex
	transactionID uint32
	connected     bool
}

// NewTCPClient 创建 TCP 客户端
func NewTCPClient(config *TCPConfig) (*TCPClient, error) {
	if config.MaxResponseMs == 0 {
		config.MaxResponseMs = 1000 * time.Millisecond
	}

	if config.Port == 0 {
		config.Port = 502
	}

	client := &TCPClient{
		config:        config,
		transactionID: 0,
	}

	return client, nil
}

// Connect 连接到服务器
func (c *TCPClient) Connect() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.connected && c.conn != nil {
		return nil
	}

	address := fmt.Sprintf("%s:%d", c.config.Host, c.config.Port)

	conn, err := net.DialTimeout("tcp", address, c.config.MaxResponseMs)
	if err != nil {
		return fmt.Errorf("connect failed: %w", err)
	}

	c.conn = conn
	c.connected = true

	if c.config.Debug {
		log.Printf("[Modbus TCP] Connected to %s", address)
	}

	return nil
}

// Close 关闭连接
func (c *TCPClient) Close() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.conn != nil {
		err := c.conn.Close()
		c.conn = nil
		c.connected = false

		if c.config.Debug {
			log.Printf("[Modbus TCP] Disconnected from %s:%d", c.config.Host, c.config.Port)
		}

		return err
	}

	return nil
}

// IsConnected 检查连接状态
func (c *TCPClient) IsConnected() bool {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	return c.connected && c.conn != nil
}

// SetMaxResponseMs 设置超时
func (c *TCPClient) SetMaxResponseMs(maxResponseMs time.Duration) {
	c.config.MaxResponseMs = maxResponseMs
}

// SetSlaveID 设置从站地址（Unit ID）
func (c *TCPClient) SetSlaveID(slaveID byte) {
	c.config.SlaveID = slaveID
}

// getNextTransactionID 获取下一个事务 ID
func (c *TCPClient) getNextTransactionID() uint16 {
	return uint16(atomic.AddUint32(&c.transactionID, 1))
}

// transaction 执行事务
func (c *TCPClient) transaction(pdu []byte) ([]byte, error) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if !c.connected || c.conn == nil {
		return nil, ErrNotConnected
	}

	// 构建 MBAP 头
	transID := c.getNextTransactionID()
	header := &MBAPHeader{
		TransactionID: transID,
		ProtocolID:    0,
		Length:        uint16(len(pdu) + 1), // PDU长度 + Unit ID
		UnitID:        c.config.SlaveID,
	}

	// 编码 MBAP 头
	mbapBytes := EncodeMBAP(header)

	// 组装完整请求（MBAP头 + PDU）
	request := append(mbapBytes, pdu...)

	if c.config.Debug {
		log.Printf("[Modbus TCP] TX: % 02X", request)
	}

	// 设置写超时
	if err := c.conn.SetWriteDeadline(time.Now().Add(c.config.MaxResponseMs)); err != nil {
		return nil, fmt.Errorf("set write deadline failed: %w", err)
	}

	// 发送请求
	n, err := c.conn.Write(request)
	if err != nil {
		c.connected = false
		return nil, fmt.Errorf("write failed: %w", err)
	}

	if n != len(request) {
		return nil, fmt.Errorf("incomplete write: %d/%d", n, len(request))
	}

	// 设置读超时
	if err := c.conn.SetReadDeadline(time.Now().Add(c.config.MaxResponseMs)); err != nil {
		return nil, fmt.Errorf("set read deadline failed: %w", err)
	}

	// 读取 MBAP 头（7字节）
	mbapHeader := make([]byte, 7)
	if _, err := io.ReadFull(c.conn, mbapHeader); err != nil {
		c.connected = false
		return nil, fmt.Errorf("read MBAP header failed: %w", err)
	}

	// 解析 MBAP 头
	respHeader, err := DecodeMBAP(mbapHeader)
	if err != nil {
		return nil, fmt.Errorf("decode MBAP header failed: %w", err)
	}

	// 验证事务 ID
	if respHeader.TransactionID != transID {
		return nil, fmt.Errorf("transaction ID mismatch: expected=%d, got=%d",
			transID, respHeader.TransactionID)
	}

	// 验证协议 ID
	if respHeader.ProtocolID != 0 {
		return nil, fmt.Errorf("invalid protocol ID: %d", respHeader.ProtocolID)
	}

	// 读取 PDU（长度 - 1，因为 Unit ID 已包含在长度中）
	pduLen := int(respHeader.Length) - 1
	if pduLen <= 0 || pduLen > 256 {
		return nil, fmt.Errorf("invalid PDU length: %d", pduLen)
	}

	responsePDU := make([]byte, pduLen)
	if _, err := io.ReadFull(c.conn, responsePDU); err != nil {
		c.connected = false
		return nil, fmt.Errorf("read PDU failed: %w", err)
	}

	if c.config.Debug {
		log.Printf("[Modbus TCP] RX: % 02X", append(mbapHeader, responsePDU...))
	}

	return responsePDU, nil
}

// 实现 Client 接口的方法
func (c *TCPClient) ReadCoils(address, quantity uint16) ([]byte, error) {
	pdu := []byte{
		FuncCodeReadCoils,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return nil, err
	}

	return ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadCoils)
}

func (c *TCPClient) ReadDiscreteInputs(address, quantity uint16) ([]byte, error) {
	pdu := []byte{
		FuncCodeReadDiscreteInputs,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return nil, err
	}

	return ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadDiscreteInputs)
}

func (c *TCPClient) ReadHoldingRegisters(address, quantity uint16) ([]byte, error) {
	pdu := []byte{
		FuncCodeReadHoldingRegisters,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return nil, err
	}

	return ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadHoldingRegisters)
}

func (c *TCPClient) ReadInputRegisters(address, quantity uint16) ([]byte, error) {
	pdu := []byte{
		FuncCodeReadInputRegisters,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return nil, err
	}

	return ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadInputRegisters)
}

func (c *TCPClient) WriteSingleCoil(address, value uint16) error {
	if value != 0 {
		value = 0xFF00
	}

	pdu := []byte{
		FuncCodeWriteSingleCoil,
		byte(address >> 8),
		byte(address),
		byte(value >> 8),
		byte(value),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return err
	}

	_, err = ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeWriteSingleCoil)
	return err
}

func (c *TCPClient) WriteSingleRegister(address, value uint16) error {
	pdu := []byte{
		FuncCodeWriteSingleRegister,
		byte(address >> 8),
		byte(address),
		byte(value >> 8),
		byte(value),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return err
	}

	_, err = ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeWriteSingleRegister)
	return err
}

func (c *TCPClient) WriteMultipleCoils(address uint16, values []bool) error {
	quantity := uint16(len(values))
	byteCount := (quantity + 7) / 8

	pdu := []byte{
		FuncCodeWriteMultipleCoils,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
		byte(byteCount),
	}

	coilBytes := make([]byte, byteCount)
	for i, val := range values {
		if val {
			coilBytes[i/8] |= 1 << (i % 8)
		}
	}

	pdu = append(pdu, coilBytes...)

	response, err := c.transaction(pdu)
	if err != nil {
		return err
	}

	_, err = ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeWriteMultipleCoils)
	return err
}

func (c *TCPClient) WriteMultipleRegisters(address uint16, values []byte) error {
	quantity := uint16(len(values) / 2)
	byteCount := byte(len(values))

	pdu := []byte{
		FuncCodeWriteMultipleRegisters,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
		byteCount,
	}

	pdu = append(pdu, values...)

	response, err := c.transaction(pdu)
	if err != nil {
		return err
	}

	_, err = ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeWriteMultipleRegisters)
	return err
}

func (c *TCPClient) ReadFileRecord(fileNumber, recordNumber, recordLength uint16) ([]byte, error) {
	pdu := []byte{
		FuncCodeReadFileRecord,
		0x07, // 字节数
		0x06, // 参考类型
		byte(fileNumber >> 8),
		byte(fileNumber),
		byte(recordNumber >> 8),
		byte(recordNumber),
		byte(recordLength >> 8),
		byte(recordLength),
	}

	response, err := c.transaction(pdu)
	if err != nil {
		return nil, err
	}

	return ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadFileRecord)
}

func (c *TCPClient) WriteFileRecord(fileNumber, recordNumber uint16, data []byte) error {
	recordLength := uint16(len(data) / 2)
	dataLength := byte(7 + len(data))

	pdu := []byte{
		FuncCodeWriteFileRecord,
		dataLength,
		0x06,
		byte(fileNumber >> 8),
		byte(fileNumber),
		byte(recordNumber >> 8),
		byte(recordNumber),
		byte(recordLength >> 8),
		byte(recordLength),
	}

	pdu = append(pdu, data...)

	response, err := c.transaction(pdu)
	if err != nil {
		return err
	}

	_, err = ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeWriteFileRecord)
	return err
}

func (c *TCPClient) ReadExceptionStatus() (byte, error) {
	pdu := []byte{FuncCodeReadExceptionStatus}

	response, err := c.transaction(pdu)
	if err != nil {
		return 0, err
	}

	data, err := ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeReadExceptionStatus)
	if err != nil {
		return 0, err
	}

	if len(data) < 1 {
		return 0, ErrResponseTooShort
	}

	return data[0], nil
}

func (c *TCPClient) GetCommEventCounter() (uint16, error) {
	pdu := []byte{FuncCodeGetCommEventCounter}

	response, err := c.transaction(pdu)
	if err != nil {
		return 0, err
	}

	data, err := ParseResponse(append([]byte{c.config.SlaveID}, response...), FuncCodeGetCommEventCounter)
	if err != nil {
		return 0, err
	}

	if len(data) < 4 {
		return 0, ErrResponseTooShort
	}

	return BytesToUint16(data[2:4]), nil
}
