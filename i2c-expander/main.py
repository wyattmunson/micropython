import utime
from machine import Pin, I2C
from PCF8574 import PCF8574
    
pcf = PCF8574(0x38, sda=12, scl=13)

# Keypad I2C setup
# i2c_expander = I2C(0, scl=Pin(13), sda=Pin(12), freq=200000)
# utime.sleep(0.1)
# I2C_ADDR2 = i2c_expander.scan()[0]
# print("INFO: Found I2C address:", hex(I2C_ADDR2))
# utime.sleep(0.1)

# i2c_port_num = 13
# pcd_address = 0x27
# pcf = PCF5874(i2c_port_num, pcd_address)

pcf.Pin(PCF8574.P0, Pin.IN)
pcf.Pin(PCF8574.P1, Pin.IN, Pin.PULL_UP)
pcf.Pin(PCF8574.P2, Pin.IN)
pcf.Pin(PCF8574.P3, Pin.IN)    

pcf.Pin(PCF8574.P7, Pin.OUT)
pcf.Pin(PCF8574.P6, Pin.OUT, 1)
pcf.Pin(PCF8574.P5, Pin.OUT, 0)
pcf.Pin(PCF8574.P4, Pin.OUT, 0)

digital_input = pcf.digital_read_all()
    
print(digital_input.p0)
print(digital_input.p1)
print(digital_input.p2)
print(digital_input.p3)
print(digital_input.p4)
print(digital_input.p5)
print(digital_input.p6)
print(digital_input.p7)

print("Additional commands")
