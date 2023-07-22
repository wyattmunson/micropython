import nrf24l01test
from machine import Pin
from utime import sleep

LED_PIN = Pin(25, Pin.OUT)

print("INFO: NRF24L01 Test, Initiator")
# LED_PIN.value(0)
print("Onning")
# LED_PIN.value(1)

LED_PIN.value(1)
sleep(0.1)
LED_PIN.value(0)
sleep(0.1)
LED_PIN.value(1)
sleep(0.1)
LED_PIN.value(0)
sleep(0.1)
LED_PIN.value(1)
sleep(0.1)
LED_PIN.value(0)

# for x in range(3):
    # LED_PIN.value(1)
    # sleep(0.1)
    # LED_PIN.value(0)

print("START UP COMPLETE")
# define pins
# csn = Pin()
nrf24l01test.initiator()
# while True:
#     print("Running")
