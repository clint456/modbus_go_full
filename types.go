package modbus

import (
	"time"
)

// RTUConfig RTU 模式配置
type RTUConfig struct {
	// 串口配置
	PortName string // 串口名称，如 "/dev/ttyUSB0", "COM1"
	BaudRate int    // 波特率：9600, 19200, 38400, 115200 等
	DataBits int    // 数据位：7, 8
	StopBits int    // 停止位：1, 2
	Parity   string // 校验位："N"(None), "E"(Even), "O"(Odd)

	// Modbus 配置
	SlaveID byte // 从站地址：1-247

	// 高级配置
	MaxResponseMs time.Duration // 最大响应超时时间，默认1000ms
	MinInterval   time.Duration // 最小请求间隔，默认 10ms

	// 调试选项
	Debug bool // 是否启用调试日志
}

// TCPConfig TCP 模式配置
type TCPConfig struct {
	// 网络配置
	Host string // 主机地址，如 "192.168.1.100"
	Port int    // 端口，默认 502

	// Modbus 配置
	SlaveID byte // 从站地址（Unit ID）：0-255

	// 高级配置
	MaxResponseMs time.Duration // 最大响应超时时间，默认1000ms
	MinInterval   time.Duration // 最小请求间隔，默认 10ms

	// 连接池配置
	MaxIdleConns    int           // 最大空闲连接数
	MaxOpenConns    int           // 最大打开连接数
	ConnMaxLifetime time.Duration // 连接最大生命周期

	// 调试选项
	Debug bool // 是否启用调试日志
}

// DefaultRTUConfig 返回默认 RTU 配置
func DefaultRTUConfig(portName string, slaveID byte) *RTUConfig {
	return &RTUConfig{
		PortName:      portName,
		BaudRate:      9600,
		DataBits:      8,
		StopBits:      1,
		Parity:        "N",
		SlaveID:       slaveID,
		MaxResponseMs: 1000 * time.Millisecond,
		MinInterval:   1 * time.Millisecond,
		Debug:         false,
	}
}

// DefaultTCPConfig 返回默认 TCP 配置
func DefaultTCPConfig(host string, slaveID byte) *TCPConfig {
	return &TCPConfig{
		Host:          host,
		Port:          502,
		SlaveID:       slaveID,
		MaxResponseMs: 1000 * time.Millisecond,
		// TODO
		MinInterval:     10 * time.Millisecond,
		MaxIdleConns:    2,
		MaxOpenConns:    5,
		ConnMaxLifetime: 30 * time.Minute,
		Debug:           false,
	}
}

// Request Modbus 请求
type Request struct {
	SlaveID      byte
	FunctionCode byte
	Address      uint16
	Quantity     uint16
	Data         []byte
}

// Response Modbus 响应
type Response struct {
	SlaveID      byte
	FunctionCode byte
	Data         []byte
}
