package main

import (
	"fmt"

	modbus "github.com/clint456/modbus_go_full"
)

func main() {
	// 测试报告中的"invalid response"
	responses := [][]byte{
		{0x01, 0x05, 0x00, 0x00, 0xFF, 0x00, 0x8C, 0x3A}, // WriteSingleCoil
		{0x01, 0x06, 0x00, 0x28, 0x30, 0x39, 0xDD, 0xD0}, // WriteSingleRegister
		{0x01, 0x06, 0x00, 0x3C, 0xFF, 0xFF, 0x48, 0x76}, // Uint16
		{0x01, 0x06, 0x00, 0x3D, 0xCF, 0xC7, 0x0C, 0x64}, // Int16
	}

	for i, resp := range responses {
		fmt.Printf("响应 %d: % 02X\n", i+1, resp)

		// 验证CRC
		isValid := modbus.VerifyCRC(resp)
		fmt.Printf("  CRC验证: %v\n", isValid)

		// 手动计算CRC
		data := resp[:len(resp)-2]
		crc := modbus.CalculateCRC(data)
		fmt.Printf("  计算的CRC: %04X\n", crc)
		fmt.Printf("  接收的CRC: %02X %02X\n", resp[len(resp)-2], resp[len(resp)-1])
		fmt.Println()
	}
}
