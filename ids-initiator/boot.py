import utime
import struct
from nrf24l01 import NRF24L01
import nrf24l01test
from machine import Pin, SPI
from utime import sleep
import time
print(time.localtime())

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
# TODO: This throws a panic if it fails
nrf = NRF24L01(spi, csn, ce, payload_size=8)
print("INFO: Configuring radio on SPI complete")

nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()
print("INFO: Radio listening")

# LOGGER
LOG_LEVEL=5
def logger(level, *args):
    if level is "FATAL" and LOG_LEVEL >= 1:
        print("FATAL:", *args)
    elif level is "ERROR" and LOG_LEVEL >= 2:
        print("ERROR:", *args)
    elif level is "WARN" and LOG_LEVEL >= 3:
        print("WARN:", *args)
    elif level is "INFO" and LOG_LEVEL >= 4:
        print("INFO:", *args)
    elif level is "DEBUG" and LOG_LEVEL >= 5:
        print("DEBUG:", *args)
    elif level is "TRACE" and LOG_LEVEL >= 6:
        print("TRACE:", *args)

    else:
        print(level, *args)

def tx_message():
    print("TX CALLED")
    tx_success = False
    tx_retry_total = 3
    tx_retries = 0

    nrf.stop_listening()
    while not tx_success and tx_retry_total > tx_retries:
        try:
            logger("DEBUG", "** Beginning request. Retry:", tx_retries)
            deviceId = 444555
            sensorState = "OPEN"
            # sensorState = sensorState.encode("utf-8")
            # sensorState = sensorState.encode()
            # byteArray = bytearray(sensorState)
            timestamp = utime.ticks_ms()
            # payload = struct.pack("isi", deviceId, sensorState, timestamp)
            payload = struct.pack("ii", deviceId, timestamp)
            nrf.send(payload)
            tx_success = True
            print("INFO: Tx success. Payload:", payload)
        except OSError:
            print("ERR: Tx failed. Error:", OSError)
            tx_retries += 1
            pass

    # start listening again
    nrf.start_listening()

    return tx_success

def sendMessage():
    # TODO: check for ACK and retry
    # confirmed = False
    # while not confirmed:
    #     nrf.stop_listening()
    nrf.stop_listening()
    ledState = ""
    tx_success = False
    tx_retry_total = 5
    tx_retries = 0
    rx_success = False

    ack_retry_total = 3
    ack_retries = 0
    ack_success = False

    # NOTE: ACK MAY NOT BE REQUIRED
    # NOTE: NRF24 may be implicitly returning an ACK response
    # NOTE: NRF24 nrf.send() return an OSError when the reciever is not found.
    while not ack_success and ack_retry_total > ack_retries:
        logger("DEEBUG", "*** Beginning main request loop. Retry:", ack_retries)
        tx_success = tx_message()
        if tx_success:
            logger("DEBUG", "Waiting for ACK response from base station")
            startTime = utime.ticks_ms()
            timeout = False
            while not nrf.any() and not timeout:
                if utime.ticks_diff(utime.ticks_ms(), startTime) > 250:
                    timeout = True
            
            if timeout:
                logger("ERROR", "Timed out waiting for ACK")
                ack_retries += 1
                # TODO: try sensing again if no ACK
            
            else:
                # TODO: parse response and validate 
                rx_success = True
                ack_success = True
                # unpack
                buf = nrf.recv()

                # unpack struct in try/except to not crash script
                try:
                    deviceId, status = struct.unpack("is", buf)
                    logger("DEBUG", "ACK response from base station:", deviceId, status)
                except TypeError:
                    logger("ERROR", "Cannot unpack ACK struct")
                except:
                    logger("ERROR", "Unknown error occured unpacking ACK struct")
        else:
            ack_retries += 1

    # TODO: move this to a separate function to send message
    # while not tx_success and tx_retry_total > tx_retries and not rx_success:
    #     try:
    #         logger("DEBUG", "** Beginning request. Retry:", tx_retries)
    #         deviceId = 444555
    #         sensorState = "OPEN"
    #         # sensorState = sensorState.encode("utf-8")
    #         # sensorState = sensorState.encode()
    #         # byteArray = bytearray(sensorState)
    #         timestamp = utime.ticks_ms()
    #         # payload = struct.pack("isi", deviceId, sensorState, timestamp)
    #         payload = struct.pack("ii", deviceId, timestamp)
    #         nrf.send(payload)
    #         tx_success = True
    #         print("INFO: Tx success. Payload:", payload)
    #     except OSError:
    #         print("ERR: Tx failed. Error:", OSError)
    #         tx_retries += 1
    #         pass

    #     # start listening again
    #     nrf.start_listening()

    #     if tx_success:
    #         # TODO: Wait for response with timeout, otherwise try again
    #         # wait for ACK response
    #         logger("DEBUG", "Waiting for ACK response from base station")
    #         startTime = utime.ticks_ms()
    #         timeout = False
    #         while not nrf.any() and not timeout:
    #             if utime.ticks_diff(utime.ticks_ms(), startTime) > 250:
    #                 timeout = True
            
    #         if timeout:
    #             logger("ERROR", "Timed out waiting for ACK")
    #             tx_retries += 1
    #             # TODO: try sensing again if no ACK
            
    #         else:
    #             # TODO: parse response and validate 
    #             rx_success = True
    #             # unpack
    #             buf = nrf.recv()

    #             # unpack struct in try/except to not crash script
    #             try:
    #                 deviceId, status = struct.unpack("is", buf)
    #                 logger("DEBUG", "ACK response from base station:", deviceId, status)
    #             except TypeError:
    #                 logger("ERROR", "Cannot unpack ACK struct")
    #             except:
    #                 logger("ERROR", "Unknown error occured unpacking ACK struct")

            # NOTE: This works when it hits above try block. Need logic to handle failure
            # logger("DEBUG", "ACK response from base station:", deviceId, status)


    if rx_success:
        logger("INFO", "Message sent and ACK recieved. Message cycle complete.")
        # print response
    else:
        logger("ERROR", "Message failed to send. Maximum retry attempts exceeded.")


    # TODO: Parse failed response


def anotherSendMessage():
    tx_success = False
    try:
        logger("DEBUG", "** Beginning request.")
        deviceId = 444555
        sensorState = "OPEN"
        # sensorState = sensorState.encode("utf-8")
        # sensorState = sensorState.encode()
        # byteArray = bytearray(sensorState)
        timestamp = utime.ticks_ms()
        # payload = struct.pack("isi", deviceId, sensorState, timestamp)
        payload = struct.pack("ii", deviceId, timestamp)
        nrf.send(payload)
        tx_success = True
        print("INFO: Tx success. Payload:", payload)
        return True
    except OSError:
        print("ERROR: Tx failed. Error:", OSError)
        return False
        pass

# sendMessage()
anotherSendMessage()
# print("INFO: Starting main loop")
# while True:
#     utime.sleep(1)
#     print("INFO: Sending message")
#     sendMessage()
#     print("INFO: Send message complete")

# HEREEEEEEEEEEEEE

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
