import utime
import struct
from nrf24l01 import NRF24L01
import nrf24l01test
from machine import Pin, SPI
from utime import sleep

# PIN SETUP
LED_PIN = Pin(25, Pin.OUT)

# Hardware SPI with explicit pin definitions
# Addresses are in little-endian format. They correspond to big-endian
# 0xf0f0f0f0e1, 0xf0f0f0f0d2
pipes = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")

spi = SPI(0, sck=Pin(2), mosi=Pin(7), miso=Pin(4))
cfg = {"spi": spi, "csn": 3, "ce": 0}

csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]
nrf = NRF24L01(spi, csn, ce, payload_size=8)

nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()

def sendMessage():
    confirmed = False
    while not confirmed:
        nrf.stop_listening()
        



# globals
connectionEstablished = False
lastHeartbeat = 0
DEVICE_ID = 1112223
DEVICE_CONNECTED = False

def flashLed(iterations:int=0):
    for _ in range(iterations):
        LED_PIN.value(1)
        sleep(0.01)
        LED_PIN.value(0)
        sleep(0.01)

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

# connect to base station
def establishConnection():
    print("Attempting to conect base station")
    cxMessage = "C" + str(DEVICE_ID)


# MAIN LOOP
# while True:

print("START UP COMPLETE")
# define pins
# csn = Pin()
# nrf24l01test.initiator()
# while True:
#     print("Running")
