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

print("INFO: Configuring radio on SPI protocol...")
csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
spi = cfg["spi"]
nrf = NRF24L01(spi, csn, ce, payload_size=8)
print("INFO: Configuring radio on SPI complete")

nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()
print("INFO: Radio listening")

# LOGGER
LOG_LEVEL=3
# FATAL
# ERROR
# WARN
# INFO
# DEBUG
# TRACE
def logger(level, *args):
    if level is "FATAL" and LOG_LEVEL >= 1:
        print("FATAL:", *args)
    elif level is "ERROR" and LOG_LEVEL >= 2:
        print("ERROR:", *args)
    elif level is "WARN" and LOG_LEVEL >= 2:
        print("WARN:", *args)
    elif level is "INFO" and LOG_LEVEL >= 2:
        print("INFO:", *args)
    elif level is "DEBUG" and LOG_LEVEL >= 2:
        print("DEBUG:", *args)
    elif level is "TRANCE" and LOG_LEVEL >= 2:
        print("TRANCE:", *args)

    else:
        print(level, *args)

def sendMessage():
    # TODO: check for ACK and retry
    # confirmed = False
    # while not confirmed:
    #     nrf.stop_listening()
    nrf.stop_listening()
    ledState = ""
    try:
        deviceId = 444555
        sensorState = "OPEN"
        # sensorState = sensorState.encode("utf-8")
        # sensorState = sensorState.encode()
        # byteArray = bytearray(sensorState)
        timestamp = utime.ticks_ms()
        # payload = struct.pack("isi", deviceId, sensorState, timestamp)
        payload = struct.pack("ii", deviceId, timestamp)
        nrf.send(payload)
        print("INFO: Tx success. Payload:", payload)
    except OSError:
        print("ERR: Tx failed. Error:", OSError)
        pass

    # start listening again
    nrf.start_listening()

    # TODO: Wait for response with timeout, otherwise try again
    startTime = utime.ticks_ms()
    timeout = False
    while not nrf.any() and not timeout:
        if utime.ticks_diff(utime.ticks_ms(), startTime) > 250:
            timeout = True
    
    if timeout:
        logger("ERROR", "Timed out waiting for ACK")
        # TODO: try sensing again if no ACK
    
    else:
        # unpack
        buf = nrf.recv()
        deviceId, status = struct.unpack("is", buf)
        logger("INFO", "Got response", deviceId, status)


        # print response
        logger("INFO")


    # TODO: Parse failed response


print("INFO: Starting main loop")
while True:
    utime.sleep(1)
    print("INFO: Sending message")
    sendMessage()
    print("INFO: Send message complete")

# globals
connectionEstablished = False
lastHeartbeat = 0
DEVICE_ID = 1112223
DEVICE_CONNECTED = False


# MAIN LOOP
# while True:

# print("START UP COMPLETE")

# define pins
# csn = Pin()
# nrf24l01test.initiator()
# while True:
#     print("Running")
