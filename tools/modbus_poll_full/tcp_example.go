package main

import (
	"fmt"
	"log"
	"time"

	modbus "github.com/clint456/modbus_go_full"
)

func main() {
	// 创建 TCP 配置
	config := &modbus.TCPConfig{
		Host:    "192.168.68.50",
		Port:    502,
		SlaveID: 1,
		Timeout: 1 * time.Second,
		Debug:   true,
	}

	// 创建客户端
	client, err := modbus.NewTCPClient(config)
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
	data, err := client.ReadHoldingRegisters(0, 10)
	if err != nil {
		log.Printf("读取失败: %v", err)
	} else {
		fmt.Printf("数据: % 02X\n", data)
	}

	// 示例 2: 写单个寄存器
	fmt.Println("\n=== 写单个寄存器 ===")
	if err := client.WriteSingleRegister(0, 9999); err != nil {
		log.Printf("写入失败: %v", err)
	} else {
		fmt.Println("写入成功")
	}

	// 示例 3: 读取线圈
	fmt.Println("\n=== 读取线圈 ===")
	coils, err := client.ReadCoils(0, 16)
	if err != nil {
		log.Printf("读取失败: %v", err)
	} else {
		fmt.Printf("线圈:  % 02X\n", coils)
	}

	// 示例 4: 批量操作
	fmt.Println("\n=== 批量操作 ===")
	for i := 0; i < 10; i++ {
		err := client.WriteSingleRegister(uint16(i), uint16(i*100))
		if err != nil {
			log.Printf("写入寄存器 %d 失败: %v", i, err)
		}
	}

	// 读取回来验证
	data, err = client.ReadHoldingRegisters(0, 10)
	if err != nil {
		log.Printf("读取失败:  %v", err)
	} else {
		fmt.Println("验证写入的数据:")
		for i := 0; i < len(data); i += 2 {
			value := modbus.BytesToUint16(data[i : i+2])
			fmt.Printf("寄存器 %d: %d\n", i/2, value)
		}
	}
}
