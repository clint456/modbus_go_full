package main

import (
	"fmt"
	"log"
	"time"

	"github.com/clint456/modbus"
)

func main() {
	// 创建 RTU 配置
	config := &modbus.RTUConfig{
		PortName: "/dev/ttyUSB0", // Linux
		// PortName:  "COM3",          // Windows
		BaudRate:    9600,
		DataBits:    8,
		StopBits:    1,
		Parity:      "N",
		SlaveID:     1,
		Timeout:     1 * time.Second,
		MinInterval: 10 * time.Millisecond,
		Debug:       true,
	}

	// 创建客户端
	client, err := modbus.NewRTUClient(config)
	if err != nil {
		log.Fatalf("创建客户端失败: %v", err)
	}
	defer client.Close()

	// 连接
	if err := client.Connect(); err != nil {
		log.Fatalf("连接失败: %v", err)
	}

	fmt.Println("连接成功！")

	// 示例 1: 读取保持寄存器
	fmt.Println("\n=== 读取保持寄存器 ===")
	data, err := client.ReadHoldingRegisters(20, 2)
	if err != nil {
		log.Printf("读取失败: %v", err)
	} else {
		fmt.Printf("原始数据: % 02X\n", data)

		// 解析为 Int32（大端）
		value, _ := modbus.BytesToInt32(data, modbus.BigEndian)
		fmt.Printf("Int32 (大端): %d\n", value)

		// 解析为 Float32（小端）
		floatValue, _ := modbus.BytesToFloat32(data, modbus.LittleEndian)
		fmt.Printf("Float32 (小端): %f\n", floatValue)
	}

	// 示例 2: 读取线圈
	fmt.Println("\n=== 读取线圈 ===")
	coils, err := client.ReadCoils(0, 10)
	if err != nil {
		log.Printf("读取线圈失败: %v", err)
	} else {
		fmt.Printf("线圈状态: % 02X\n", coils)
		for i := 0; i < 10; i++ {
			bit := (coils[i/8] >> (i % 8)) & 1
			fmt.Printf("线圈 %d:  %d\n", i, bit)
		}
	}

	// 示例 3: 写单个寄存器
	fmt.Println("\n=== 写单个寄存器 ===")
	if err := client.WriteSingleRegister(30, 1234); err != nil {
		log.Printf("写入失败: %v", err)
	} else {
		fmt.Println("写入成功")
	}

	// 示例 4: 写多个寄存器
	fmt.Println("\n=== 写多个寄存器 ===")
	writeData := []byte{0x12, 0x34, 0x56, 0x78}
	if err := client.WriteMultipleRegisters(40, writeData); err != nil {
		log.Printf("写入失败: %v", err)
	} else {
		fmt.Println("写入成功")
	}

	// 示例 5: 读取输入寄存器
	fmt.Println("\n=== 读取输入寄存器 ===")
	inputData, err := client.ReadInputRegisters(0, 5)
	if err != nil {
		log.Printf("读取失败: %v", err)
	} else {
		fmt.Printf("输入寄存器: % 02X\n", inputData)
		for i := 0; i < len(inputData); i += 2 {
			value := modbus.BytesToUint16(inputData[i : i+2])
			fmt.Printf("寄存器 %d: %d\n", i/2, value)
		}
	}

	// 示例 6: 循环读取
	fmt.Println("\n=== 循环读取 ===")
	for i := 0; i < 5; i++ {
		data, err := client.ReadHoldingRegisters(0, 1)
		if err != nil {
			log.Printf("读取失败: %v", err)
		} else {
			value := modbus.BytesToUint16(data)
			fmt.Printf("第 %d 次读取: %d\n", i+1, value)
		}
		time.Sleep(100 * time.Millisecond)
	}
}
