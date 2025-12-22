package modbus

import (
	"encoding/binary"
	"fmt"
)

// ============= CRC 计算 =============

// CalculateCRC 计算 CRC-16/MODBUS
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

// VerifyCRC 验证 CRC
func VerifyCRC(data []byte) bool {
	if len(data) < 2 {
		return false
	}

	calculated := CalculateCRC(data[:len(data)-2])
	received := uint16(data[len(data)-2]) | uint16(data[len(data)-1])<<8

	return calculated == received
}

// AppendCRC 添加 CRC 到数据末尾
func AppendCRC(data []byte) []byte {
	crc := CalculateCRC(data)
	return append(data, byte(crc), byte(crc>>8))
}

// ============= PDU 构建 =============

// BuildReadRequest 构建读请求 (功能码 1, 2, 3, 4)
func BuildReadRequest(slaveID, funcCode byte, address, quantity uint16) []byte {
	pdu := []byte{
		slaveID,
		funcCode,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
	}
	return pdu
}

// BuildWriteSingleRequest 构建写单个请求 (功能码 5, 6)
func BuildWriteSingleRequest(slaveID, funcCode byte, address, value uint16) []byte {
	pdu := []byte{
		slaveID,
		funcCode,
		byte(address >> 8),
		byte(address),
		byte(value >> 8),
		byte(value),
	}
	return pdu
}

// BuildWriteMultipleCoilsRequest 构建写多个线圈请求 (功能码 15)
func BuildWriteMultipleCoilsRequest(slaveID byte, address uint16, values []bool) []byte {
	quantity := uint16(len(values))
	byteCount := (quantity + 7) / 8

	pdu := []byte{
		slaveID,
		FuncCodeWriteMultipleCoils,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
		byte(byteCount),
	}

	// 转换布尔数组为字节
	coilBytes := make([]byte, byteCount)
	for i, val := range values {
		if val {
			coilBytes[i/8] |= 1 << (i % 8)
		}
	}

	pdu = append(pdu, coilBytes...)
	return pdu
}

// BuildWriteMultipleRegistersRequest 构建写多个寄存器请求 (功能码 16)
func BuildWriteMultipleRegistersRequest(slaveID byte, address uint16, values []byte) []byte {
	quantity := uint16(len(values) / 2)
	byteCount := byte(len(values))

	pdu := []byte{
		slaveID,
		FuncCodeWriteMultipleRegisters,
		byte(address >> 8),
		byte(address),
		byte(quantity >> 8),
		byte(quantity),
		byteCount,
	}

	pdu = append(pdu, values...)
	return pdu
}

// BuildReadFileRecordRequest 构建读文件记录请求 (功能码 20)
func BuildReadFileRecordRequest(slaveID byte, fileNumber, recordNumber, recordLength uint16) []byte {
	pdu := []byte{
		slaveID,
		FuncCodeReadFileRecord,
		0x07, // 字节数（固定7字节）
		0x06, // 参考类型（固定0x06）
		byte(fileNumber >> 8),
		byte(fileNumber),
		byte(recordNumber >> 8),
		byte(recordNumber),
		byte(recordLength >> 8),
		byte(recordLength),
	}
	return pdu
}

// BuildWriteFileRecordRequest 构建写文件记录请求 (功能码 21)
func BuildWriteFileRecordRequest(slaveID byte, fileNumber, recordNumber uint16, data []byte) []byte {
	recordLength := uint16(len(data) / 2)
	dataLength := byte(7 + len(data))

	pdu := []byte{
		slaveID,
		FuncCodeWriteFileRecord,
		dataLength,
		0x06, // 参考类型
		byte(fileNumber >> 8),
		byte(fileNumber),
		byte(recordNumber >> 8),
		byte(recordNumber),
		byte(recordLength >> 8),
		byte(recordLength),
	}

	pdu = append(pdu, data...)
	return pdu
}

// ============= 响应解析 =============

// ParseResponse 解析响应
func ParseResponse(response []byte, expectedFuncCode byte) ([]byte, error) {
	if len(response) < 2 {
		return nil, ErrResponseTooShort
	}

	_ = response[0] // slaveID, 不需要使用
	funcCode := response[1]

	// 检查异常响应
	if funcCode&0x80 != 0 {
		if len(response) < 3 {
			return nil, ErrResponseTooShort
		}
		return nil, &ModbusError{
			FunctionCode:  funcCode & 0x7F,
			ExceptionCode: response[2],
		}
	}

	// 验证功能码
	if funcCode != expectedFuncCode {
		return nil, fmt.Errorf("%w: expected=0x%02X, got=0x%02X",
			ErrUnexpectedResponse, expectedFuncCode, funcCode)
	}

	// 提取数据
	switch funcCode {
	case FuncCodeReadCoils, FuncCodeReadDiscreteInputs,
		FuncCodeReadHoldingRegisters, FuncCodeReadInputRegisters:
		if len(response) < 3 {
			return nil, ErrResponseTooShort
		}
		byteCount := int(response[2])
		if len(response) < 3+byteCount {
			return nil, ErrResponseTooShort
		}
		return response[3 : 3+byteCount], nil

	case FuncCodeWriteSingleCoil, FuncCodeWriteSingleRegister,
		FuncCodeWriteMultipleCoils, FuncCodeWriteMultipleRegisters:
		return response[2:], nil

	case FuncCodeReadFileRecord:
		if len(response) < 4 {
			return nil, ErrResponseTooShort
		}
		dataLength := int(response[3])
		if len(response) < 4+dataLength {
			return nil, ErrResponseTooShort
		}
		return response[4 : 4+dataLength], nil

	case FuncCodeWriteFileRecord:
		return response[2:], nil

	case FuncCodeReadExceptionStatus:
		if len(response) < 3 {
			return nil, ErrResponseTooShort
		}
		return response[2:3], nil

	case FuncCodeGetCommEventCounter:
		if len(response) < 6 {
			return nil, ErrResponseTooShort
		}
		return response[2:6], nil

	default:
		return response[2:], nil
	}
}

// ============= MBAP 头处理（TCP 使用）=============

// MBAPHeader MBAP 头（Modbus Application Protocol Header）
type MBAPHeader struct {
	TransactionID uint16
	ProtocolID    uint16
	Length        uint16
	UnitID        byte
}

// EncodeMBAP 编码 MBAP 头
func EncodeMBAP(header *MBAPHeader) []byte {
	buf := make([]byte, 7)
	binary.BigEndian.PutUint16(buf[0:2], header.TransactionID)
	binary.BigEndian.PutUint16(buf[2:4], header.ProtocolID)
	binary.BigEndian.PutUint16(buf[4:6], header.Length)
	buf[6] = header.UnitID
	return buf
}

// DecodeMBAP 解码 MBAP 头
func DecodeMBAP(data []byte) (*MBAPHeader, error) {
	if len(data) < 7 {
		return nil, ErrResponseTooShort
	}

	header := &MBAPHeader{
		TransactionID: binary.BigEndian.Uint16(data[0:2]),
		ProtocolID:    binary.BigEndian.Uint16(data[2:4]),
		Length:        binary.BigEndian.Uint16(data[4:6]),
		UnitID:        data[6],
	}

	return header, nil
}
