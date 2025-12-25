// Package modbus provides a pure Go implementation of Modbus protocol
// supporting both RTU and TCP modes without requiring RS485 ioctl.
//
// This package is docs/DESIGNed to work with USB-to-Serial converters (like CH340)
// that handle RS485 direction control in hardware.
package modbus

import (
	"time"
)

// Client Modbus 客户端接口
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
	SetMaxResponseMs(maxResponseMs time.Duration)
	SetSlaveID(slaveID byte)
}

// Modbus 功能码常量
const (
	// 位访问
	FuncCodeReadCoils          byte = 0x01
	FuncCodeReadDiscreteInputs byte = 0x02
	FuncCodeWriteSingleCoil    byte = 0x05
	FuncCodeWriteMultipleCoils byte = 0x0F

	// 16位寄存器访问
	FuncCodeReadHoldingRegisters   byte = 0x03
	FuncCodeReadInputRegisters     byte = 0x04
	FuncCodeWriteSingleRegister    byte = 0x06
	FuncCodeWriteMultipleRegisters byte = 0x10

	// 文件记录
	FuncCodeReadFileRecord  byte = 0x14
	FuncCodeWriteFileRecord byte = 0x15

	// 诊断
	FuncCodeReadExceptionStatus byte = 0x07
	FuncCodeDiagnostics         byte = 0x08
	FuncCodeGetCommEventCounter byte = 0x0B
	FuncCodeGetCommEventLog     byte = 0x0C
	FuncCodeReportSlaveID       byte = 0x11

	// 高级操作
	FuncCodeMaskWriteRegister          byte = 0x16
	FuncCodeReadWriteMultipleRegisters byte = 0x17
	FuncCodeReadFIFOQueue              byte = 0x18
	FuncCodeReadDeviceIdentification   byte = 0x2B
)

// Endianness 字节序类型
type Endianness int

const (
	// LittleEndian 小端模式（低地址寄存器为数据低16位）
	LittleEndian Endianness = 1

	// BigEndian 大端模式（低地址寄存器为数据高16位）
	BigEndian Endianness = 2

	// LittleEndianSwap 小端字节交换（小端模式 + 寄存器内部字节交换）
	LittleEndianSwap Endianness = 3

	// BigEndianSwap 大端字节交换（大端模式 + 寄存器内部字节交换）
	BigEndianSwap Endianness = 4
)

// Version 包版本
const Version = "1.0.0"
