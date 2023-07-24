import struct
import utime
import ujson
import json
from machine import Pin, SPI
from nrf24l01 import NRF24L01

class Communicator:
    def __init__(self, another):
        self.pipesAreSet = False
        self.another = another
        print("Created")
    

    def logger(self, level, *args):
        LOG_LEVEL=5
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

    def printMessage(self, text):
        print("Existing")
        print("ANOTHER", self.another)
        print("TEXT", text)


    def configureWireless(self, sck, mosi, miso, csn, ce):
        self.logger("DEBUG", "Configuring NRF24L01 pins...")
        # check setPipes was set
        if not self.pipesAreSet:
            raise ValueError("Addresses are not set. Call setPipes() first.")
        if not hasattr(self, "tx_address"):
            print("ERROR: Call setPipes() to define transmit address")
            raise ValueError("Transmit not set. See more information above.")
        # sck_pin = 3
        try:
            # spi = SPI(0, sck=Pin(2), mosi=Pin(7), miso=Pin(4))
            spi = SPI(0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(4))
            cfg = {"spi": spi, "csn": 3, "ce": 0}
        except ValueError as e:
            # spi = "test"
            print("Upstream error: ", e)
            # TODO: in error show pin number and more dynamic error message
            upstream_error = str(e)
            display_error = None
            if "SCK" in upstream_error:
                raise ValueError("Pin %i is not a %s pin. Choose a different pin or verify pin number is correct."%(sck, "SCK"))
            if "MOSI" in upstream_error:
                raise ValueError("Pin %i is not a %s pin. Choose a different pin or verify pin number is correct."%(mosi, "MOSI/COSI"))
            # This doesn't appear to thrown an error
            if "MISO" in upstream_error:
                raise ValueError("Pin %i is not a %s/CIPO pin. Choose a different pin or verify pin number is correct."%(miso, "MISO/CIPO"))
            # This doesn't appear to thrown an error
            if "CSN" in upstream_error:
                raise ValueError("Pin %i is not a %s pin. Choose a different pin or verify pin number is correct."%(csn, "CSN"))
            raise ValueError("%s. The pin number provided is not used for that protocol. Choose a differnt pin or verify pin number."%(e))

        # spi can be defined in "try"
        # spi can be defined in "except" or raise Error
        print(spi)

        # setup NRF
        csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
        ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
        spi = cfg["spi"]
        # nrf = NRF24L01(spi, csn, ce, payload_size=8)
        try:
            nrf = NRF24L01(spi, csn, ce, payload_size=8)
        except OSError as e:
            self.logger("ERROR", "Upstream error:", str(e))
            self.logger("ERROR", "Unable to communicate with NRF24L01 module. Verify pins are connected correctly.")
            raise OSError("Unable to communicate with NRF24L01 module. Verify pins are connected correctly.")
        except Exception as e:
            self.logger("ERROR", "Upstream error:", str(e))
            self.logger("ERROR", "Unknown error occured.")
            # self.nrf = False
            raise ValueError("Unable to define nrf object")
        self.nrf = nrf
        # if not self.transmit or not self.receive:
        #     print("ERROR: Transmit or recieve not set")
        #     raise ValueError("Transmit not set")
        # # receive = self.receive
        # # transmit = self.transmit
        # print("Configuring wireless network")
        # if not self.receive:
        #     print("Transmit address not set")
        # else:
        #     print("RECIEVE PIPE", self.receive)
    

    def setAddress(self, transmit_address, receive_address):
        self.logger("DEBUG", "Setting up addresses...")
        # check for variables
        # if not tra
        print("Setting pipes")
        self.tx_address = transmit_address
        self.rx_address = receive_address
        self.pipesAreSet = True
        self.logger("DEBUG", "Setup address completed")
    

    def open_pipes(self):
        if not hasattr(self, "nrf"):
            print("None")
            raise ValueError("NRF does not exist. Call SET_UP_PINS first")
        self.nrf.open_tx_pipe(self.tx_address)
        self.nrf.open_rx_pipe(1, self.rx_address)
        self.nrf.start_listening()
    

    def send_message(self, device_id, payload):
        self.logger("DEBUG", "** Beginning request.")
        # BELOW does not seem to matter - not sure of use
        self.nrf.stop_listening()
        # TODO: Dynamically get input
        # TODO: get things other than strings
        deviceId = 444555
        timestamp = utime.ticks_ms()

        # dumped_payload = json.dumps(payload)
        # binary = ' '.join(format(ord(letter), 'b') for letter in dumped_payload)
        dumped_payload = json.dumps(payload).encode()

        # encoded_topic = topic.encode()
        # encoded_sensor_state = sensor_state.encode()
        # print(encoded_topic)
        # main_struct = struct.pack("i", deviceId)


        try:
            # self.nrf.send(struct.pack("ii", deviceId, timestamp))
            # self.nrf.send(struct.pack("iissss", deviceId, timestamp, encoded_sensor_state))
            # self.nrf.send(struct.pack("4s", encoded_sensor_state))
            # self.nrf.send(dumped_payload)

            # another
            # dumped = json.dumps(payload)
            # formatter = str(len(dumped)) + "s"
            # self.nrf.send(struct.pack(formatter, dumped))
            # self.logger("INFO", "Message sent")
            # dumped = "".join((ujson.dumps(payload), '\n'))
            # encoded = dumped.encode()
            # self.nrf.send(encoded)
            # self.logger("INFO", "Message sent")
            bytes = bytearray()
            for key, value in payload.items():
                bytes += struct.pack("!h", len(key))
                bytes += key.encode("utf-8")
                bytes += struct.pack("!h", len(value))
                bytes += value.encode("utf-8")
            self.nrf.send(bytes)

            
            print("SEND DONE", self.nrf.send_done())
        except OSError as e:
            self.logger("ERROR", "Upastream error:", e)
            self.logger("ERROR", "Failed to send")
            pass
        except Exception as e:
            print("Unidentified error:", e)

        self.nrf.start_listening()
        
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())
        # utime.sleep(0.1)
        # print("SEND DONE", self.nrf.send_done())

        # try:
        #     self.logger("DEBUG", "** Beginning request.")
        #     deviceId = 444555
        #     sensorState = "OPEN"
        #     # sensorState = sensorState.encode("utf-8")
        #     # sensorState = sensorState.encode()
        #     # byteArray = bytearray(sensorState)
        #     timestamp = utime.ticks_ms()
        #     # payload = struct.pack("isi", deviceId, sensorState, timestamp)
        #     payload = struct.pack("ii", deviceId, timestamp)
        #     self.nrf.send(payload)
        #     tx_success = True
        #     print("INFO: Tx success. Payload:", payload)
        #     return True
        # except OSError:
        #     print("ERROR: Tx failed. Error:", OSError)
        #     return False
        # except:
        #     print("Any other error")

        # END OF SEND MESSAGE



comm = Communicator("test")
thinger = comm.printMessage("TO PRINTER")
# comm.setPipes()
tx_a = b"\xe1\xf0\xf0\xf0\xf0"
rx_a = b"\xd2\xf0\xf0\xf0\xf0"
# comm.setAddress(b"\xd2\xf0\xf0\xf0\xf0", b"\xe1\xf0\xf0\xf0\xf0")
comm.setAddress(tx_a, rx_a)
comm.configureWireless(sck=2, mosi=7, miso=4, csn=3, ce=0)
comm.open_pipes()
payload = {"deviceId": "123123123", "another": "tester"}
comm.send_message(123456, payload)
# comm.configureWireless(sck=2, mosi=7, miso=4, csn=3, ce=0)