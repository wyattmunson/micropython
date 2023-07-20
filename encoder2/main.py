import time
from machine import Pin

rotaryA = Pin(1, Pin.IN, Pin.PULL_DOWN)
rotaryB = Pin(12, Pin.IN, Pin.PULL_DOWN)

while True:
    print(rotaryA.value(), end='')
    print(rotaryB.value())
    time.sleep(.1)
