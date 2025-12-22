package modbus

import (
	"fmt"
)

// ModbusError Modbus 错误
type ModbusError struct {
	FunctionCode  byte
	ExceptionCode byte
}

func (e *ModbusError) Error() string {
	return fmt.Sprintf("modbus exception: function=0x%02X, exception=0x%02X (%s)",
		e.FunctionCode, e.ExceptionCode, e.ExceptionString())
}

// ExceptionString 返回异常描述
func (e *ModbusError) ExceptionString() string {
	switch e.ExceptionCode {
	case ExceptionIllegalFunction:
		return "Illegal Function"
	case ExceptionIllegalDataAddress:
		return "Illegal Data Address"
	case ExceptionIllegalDataValue:
		return "Illegal Data Value"
	case ExceptionSlaveDeviceFailure:
		return "Slave Device Failure"
	case ExceptionAcknowledge:
		return "Acknowledge"
	case ExceptionSlaveDeviceBusy:
		return "Slave Device Busy"
	case ExceptionMemoryParityError:
		return "Memory Parity Error"
	case ExceptionGatewayPathUnavailable:
		return "Gateway Path Unavailable"
	case ExceptionGatewayTargetFailed:
		return "Gateway Target Device Failed to Respond"
	default:
		return "Unknown Exception"
	}
}

// Modbus 异常码
const (
	ExceptionIllegalFunction        byte = 0x01
	ExceptionIllegalDataAddress     byte = 0x02
	ExceptionIllegalDataValue       byte = 0x03
	ExceptionSlaveDeviceFailure     byte = 0x04
	ExceptionAcknowledge            byte = 0x05
	ExceptionSlaveDeviceBusy        byte = 0x06
	ExceptionMemoryParityError      byte = 0x08
	ExceptionGatewayPathUnavailable byte = 0x0A
	ExceptionGatewayTargetFailed    byte = 0x0B
)

// 自定义错误
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
