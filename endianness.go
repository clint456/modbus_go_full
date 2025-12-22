package modbus

import (
	"encoding/binary"
	"fmt"
	"math"
)

// BytesToInt16 字节转 Int16
func BytesToInt16(data []byte) int16 {
	return int16(binary.BigEndian.Uint16(data))
}

// BytesToUint16 字节转 Uint16
func BytesToUint16(data []byte) uint16 {
	return binary.BigEndian.Uint16(data)
}

// BytesToInt32 字节转 Int32（支持字节序）
func BytesToInt32(data []byte, endianness Endianness) (int32, error) {
	if len(data) < 4 {
		return 0, fmt.Errorf("insufficient data for int32: need 4 bytes, got %d", len(data))
	}

	var value uint32

	switch endianness {
	case LittleEndian:
		// 低地址寄存器为低16位：[B C D A] -> ABCD
		value = uint32(data[2])<<24 | uint32(data[3])<<16 | uint32(data[0])<<8 | uint32(data[1])

	case BigEndian:
		// 低地址寄存器为高16位：[A B C D] -> ABCD
		value = uint32(data[0])<<24 | uint32(data[1])<<16 | uint32(data[2])<<8 | uint32(data[3])

	case LittleEndianSwap:
		// 小端 + 字节交换：[C D A B] -> ABCD
		value = uint32(data[1])<<24 | uint32(data[0])<<16 | uint32(data[3])<<8 | uint32(data[2])

	case BigEndianSwap:
		// 大端 + 字节交换：[B A D C] -> ABCD
		value = uint32(data[3])<<24 | uint32(data[2])<<16 | uint32(data[1])<<8 | uint32(data[0])

	default:
		return 0, fmt.Errorf("unsupported endianness: %d", endianness)
	}

	return int32(value), nil
}

// BytesToUint32 字节转 Uint32（支持字节序）
func BytesToUint32(data []byte, endianness Endianness) (uint32, error) {
	if len(data) < 4 {
		return 0, fmt.Errorf("insufficient data for uint32: need 4 bytes, got %d", len(data))
	}

	var value uint32

	switch endianness {
	case LittleEndian:
		value = uint32(data[2])<<24 | uint32(data[3])<<16 | uint32(data[0])<<8 | uint32(data[1])

	case BigEndian:
		value = uint32(data[0])<<24 | uint32(data[1])<<16 | uint32(data[2])<<8 | uint32(data[3])

	case LittleEndianSwap:
		value = uint32(data[1])<<24 | uint32(data[0])<<16 | uint32(data[3])<<8 | uint32(data[2])

	case BigEndianSwap:
		value = uint32(data[3])<<24 | uint32(data[2])<<16 | uint32(data[1])<<8 | uint32(data[0])

	default:
		return 0, fmt.Errorf("unsupported endianness: %d", endianness)
	}

	return value, nil
}

// BytesToFloat32 字节转 Float32（支持字节序）
func BytesToFloat32(data []byte, endianness Endianness) (float32, error) {
	value, err := BytesToUint32(data, endianness)
	if err != nil {
		return 0, err
	}
	return math.Float32frombits(value), nil
}

// Int16ToBytes Int16 转字节
func Int16ToBytes(value int16) []byte {
	buf := make([]byte, 2)
	binary.BigEndian.PutUint16(buf, uint16(value))
	return buf
}

// Uint16ToBytes Uint16 转字节
func Uint16ToBytes(value uint16) []byte {
	buf := make([]byte, 2)
	binary.BigEndian.PutUint16(buf, value)
	return buf
}

// Int32ToBytes Int32 转字节（支持字节序）
func Int32ToBytes(value int32, endianness Endianness) ([]byte, error) {
	return Uint32ToBytes(uint32(value), endianness)
}

// Uint32ToBytes Uint32 转字节（支持字节序）
func Uint32ToBytes(value uint32, endianness Endianness) ([]byte, error) {
	buf := make([]byte, 4)

	switch endianness {
	case LittleEndian:
		buf[0] = byte(value >> 8)
		buf[1] = byte(value)
		buf[2] = byte(value >> 24)
		buf[3] = byte(value >> 16)

	case BigEndian:
		buf[0] = byte(value >> 24)
		buf[1] = byte(value >> 16)
		buf[2] = byte(value >> 8)
		buf[3] = byte(value)

	case LittleEndianSwap:
		buf[0] = byte(value >> 16)
		buf[1] = byte(value >> 24)
		buf[2] = byte(value)
		buf[3] = byte(value >> 8)

	case BigEndianSwap:
		buf[0] = byte(value)
		buf[1] = byte(value >> 8)
		buf[2] = byte(value >> 16)
		buf[3] = byte(value >> 24)

	default:
		return nil, fmt.Errorf("unsupported endianness: %d", endianness)
	}

	return buf, nil
}

// Float32ToBytes Float32 转字节（支持字节序）
func Float32ToBytes(value float32, endianness Endianness) ([]byte, error) {
	bits := math.Float32bits(value)
	return Uint32ToBytes(bits, endianness)
}
