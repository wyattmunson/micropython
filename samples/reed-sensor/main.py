from machine import Pin, PWM
import utime
from utime import sleep

reedSwitch = Pin(5, Pin.IN, Pin.PULL_UP)

while True:
    if reedSwitch.value() == 0:
        print("Value is 0")
    else:
        print("Value is 1")
    
    sleep(0.1)