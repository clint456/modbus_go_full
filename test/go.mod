module test

go 1.25.5

replace github.com/clint456/modbus => ../

require github.com/clint456/modbus v0.0.0-00010101000000-000000000000

require (
	github.com/tarm/serial v0.0.0-20180830185346-98f6abe2eb07 // indirect
	golang.org/x/sys v0.15.0 // indirect
)
