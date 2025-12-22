package modbus

import (
	"fmt"
)

// NewClient 创建 Modbus 客户端
func NewClient(protocol string, config interface{}) (Client, error) {
	switch protocol {
	case "rtu", "RTU", "modbusRtu":
		rtuConfig, ok := config.(*RTUConfig)
		if !ok {
			return nil, fmt.Errorf("invalid RTU config type")
		}
		return NewRTUClient(rtuConfig)

	case "tcp", "TCP", "modbusTcp":
		tcpConfig, ok := config.(*TCPConfig)
		if !ok {
			return nil, fmt.Errorf("invalid TCP config type")
		}
		return NewTCPClient(tcpConfig)

	default:
		return nil, fmt.Errorf("unsupported protocol: %s", protocol)
	}
}
