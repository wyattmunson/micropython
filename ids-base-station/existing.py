import utime
import struct
from nrf24l01 import NRF24L01

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

print("== IDS BASE STATION ==")
print("INFO: Radio started without issue")

while True:
    if nrf.any():
        while nrf.any():
            # get message from buffer
            buf = nrf.recv()
            deviceId, sensorState, timestamp = struct.unpack("isi", buf)
            print("Received:", deviceId, sensorState, timestamp)

        # give sensor time to enter response mode
        utime.sleep_ms(10)
        nrf.stop_listening()
        try:
            nrf.send(struct.pack("is", "deviceId", "ACK"))
        except OSError:
            pass
        print("Sent ACK")

        # TODO: save response
        # recordMotion()
        nrf.start_listening()

# ALARM / SECURITY BELOW

# GLOBAL VARIABLES
# START: new proposals
SYSTEM_ARMED = False
SYSTEM_TRIGGERED = False
SYSTEM_SHOULD_ARM = False
SYSTEM_IS_ARMING = False
# END: new proposals

# SECURITY GLOBALS
systemArmed = False
systemTriggered = False
systemWarning = False
shouldArm = False
shouldTrigger = False
armTimeout = 0
passcode = "1111"
passcodeDigitLength = 4
WARNING_TIMEOUT=10000
WARNING_TIME=0

# TODO: Keypad setup? Not necessary for base station

# TODO: I2C setup? Not necessary for base station?

# ARM WORKFLOW

# TOGGLE TRIGGER

# RESOLVE ALARM

# DISARM WORKFLOW

# GET PASSCODE INPUT

# TODO: LOADING SCREENS AND RENDERING

# TODO: WRITE LOG MESSAGE. Save and/or API Call

# SENSOR HANDLING, get sensor input



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
# nrf24l01test.responder()
# while True:
#     print("Running")