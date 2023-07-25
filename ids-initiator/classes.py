import struct
import utime
import json
import binascii
from machine import Pin, SPI
from nrf24l01 import NRF24L01

class Communicator:
    def __init__(self):
        self.addresses_are_set = False
        self.pins_configured = False
        self.pipes_open = False
    

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


    def configure_pins(self, sck, mosi, miso, csn, ce):
        self.logger("DEBUG", "Configuring NRF24L01 pins...")
        # check setPipes was set
        if not self.addresses_are_set:
            raise ValueError("Addresses are not set. Call setPipes() first.")

        try:
            spi = SPI(0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
            cfg = {"spi": spi, "csn": csn, "ce": ce}
        except ValueError as e:
            upstream_error = str(e)
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

        self.logger("DEBUG", "SPI configured:", spi)

        # setup NRF
        csn = Pin(cfg["csn"], mode=Pin.OUT, value=1)
        ce = Pin(cfg["ce"], mode=Pin.OUT, value=0)
        spi = cfg["spi"]
        try:
            nrf = NRF24L01(spi, csn, ce, payload_size=8)
        except OSError as e:
            self.logger("ERROR", "Upstream error:", str(e))
            self.logger("ERROR", "Unable to communicate with NRF24L01 module. Verify pins are connected correctly.")
            raise OSError("Unable to communicate with NRF24L01 module. Verify pins are connected correctly.")
        except Exception as e:
            self.logger("ERROR", "Unknown error occured. Upstream error:", str(e))
            raise ValueError("Unable to define nrf object")
        
        self.pins_configured = True
        self.nrf = nrf


    def validate_address(self, tx, add_type):
        if not isinstance(tx, bytes):
            raise TypeError("Error: Address is not a bytes datatype.")

        if len(tx) != 5:
            raise ValueError("Error: Address for %s should be exactly 5 bytes"%(add_type))
        
        for byte in tx:
            if not 0x00 <= byte < 0xFF:
                raise ValueError("Error: Every byte in %s address should be a hexadecimal charachter"%(add_type))
    

    def set_addresses(self, transmit_address, receive_address):
        self.logger("DEBUG", "Setting up addresses...")
        self.validate_address(transmit_address, "transmit")
        self.validate_address(receive_address, "receive")

        # TODO: Provide handling for dec/oct/hex address formats

        # Set addresses to self
        self.tx_address = transmit_address
        self.rx_address = receive_address
        self.addresses_are_set = True
        self.logger("DEBUG", "Setup address completed")


    def open_pipes(self):
        # TODO: Does this need to be separate? Can this be done in configure_pins()?
        if not self.pins_configured:
            raise ValueError("Pins not configured. Call configure_pins() first")

        self.pipes_open = True
        self.nrf.open_tx_pipe(self.tx_address)
        self.nrf.open_rx_pipe(1, self.rx_address)
        self.nrf.start_listening()
    

    def send_message(self, device_id, sensor_state):
        self.logger("INFO", "Transmitting message...")
        if not self.pipes_open:
            raise ValueError("Pipes must be open before sending message. Call open_pipes() first.")
        
        self.nrf.stop_listening()
        deviceId = 444555
        timestamp = utime.ticks_ms()

        sample_obj = { "device_id": 123123123, "sensor_state": "OPEN"}
        text_obj = json.dumps(sample_obj)
        print("TEXT OBJ", (text_obj))
        chunked_array = []
        # for x in range(len(text_obj)):
        for x in range(0, len(text_obj), 8):
            print("X is", x)
            print(text_obj[x:x + 8])


        try:
            # WORKING
            # self.nrf.send(struct.pack("ii", device_id, sensor_state))
            
            # test_payload = {"deviceId": "123123", "sensor_state": "OPEN"}
            # converted = bytearray(test_payload)
            # payload = ["device_id", 123123, "sensor_state", "OPEN"]
            # payload_bytes = bytes(payload)
            # payload = ["device_id", "123123", "sensor_state", "OPEN"]
            payload = "here is some rather longer text to send for"
            # payload = payload.encode()
            print(len(payload))
            format_string = "I%ds" % len(payload)
            # to_send = struct.pack(format_string, len(payload), payload.encode())
            to_send = struct.pack("ssssssss", payload[0], payload[1], payload[2], payload[3], payload[4], payload[5], payload[6], payload[7])
            
            self.nrf.send(to_send)
            self.logger("INFO", "Message transmitted successfully")
        except OSError as e:
            self.logger("ERROR", "Upastream error:", e)
            self.logger("ERROR", "Failed to send")
            pass
        except Exception as e:
            print("Unidentified error:", e)

        self.nrf.start_listening()
    
    def send_message_chunked(self, json_payload):
        self.logger("INFO", "Transmitting message with chunks...")
        if not self.pipes_open:
            raise ValueError("Pipes must be open before sending message. Call open_pipes() first.")
        
        self.nrf.stop_listening()
        deviceId = 444555
        timestamp = utime.ticks_ms()

        sample_obj = { "device_id": 123123123, "sensor_state": "OPEN"}
        text_obj = json.dumps(sample_obj)
        print("TEXT OBJ:", text_obj)
        text_obj = text_obj.encode()
        print("TEXT OBJ ENCODED:", text_obj)
        as_bytes = binascii.b2a_base64(text_obj)
        print("TEXT OBJ AS BINARY:", as_bytes, type(as_bytes))
        chunks = []
        chunk_size = 20
        for i in range(0, len(as_bytes), chunk_size):
            chunks.append(as_bytes[i:i + chunk_size])
        # chunks = chunk_data(as_bytes, 1024)
        for chunk in chunks:
            print(chunk)
        chunked_array = []

        self.logger("INFO", "Transmitting message in %i chunks..." % (len(chunks)))

        for index, chunk in enumerate(chunks):
            try:
                self.logger("DEBUG", "Sending chunk %i..." % (index))
                self.nrf.send(chunk)
                self.logger("INFO", "Message transmitted successfully")
            except OSError as e:
                self.logger("ERROR", "Upastream error:", e)
                self.logger("ERROR", "Failed to send")
                pass
            except Exception as e:
                print("Unidentified error:", e)

        self.nrf.start_listening()
    



    def send_chunked(self, message):
        for x in range(len(message)):
            try:
                # WORKING
                # self.nrf.send(struct.pack("ii", device_id, sensor_state))

                # test_payload = {"deviceId": "123123", "sensor_state": "OPEN"}
                # converted = bytearray(test_payload)
                # payload = ["device_id", 123123, "sensor_state", "OPEN"]
                # payload_bytes = bytes(payload)
                # payload = ["device_id", "123123", "sensor_state", "OPEN"]
                # payload = "here is some rather longer text to send for"
                payload = message[x]
                # payload = payload.encode()
                print(len(payload))
                format_string = "I%ds" % len(payload)
                # to_send = struct.pack(format_string, len(payload), payload.encode())
                to_send = struct.pack("ssssssss", payload[0], payload[1], payload[2], payload[3], payload[4], payload[5], payload[6], payload[7])

                self.nrf.send(to_send)
                self.logger("INFO", "Message transmitted successfully")
                utime.sleep_ms(270)
            except OSError as e:
                self.logger("ERROR", "Upastream error:", e)
                self.logger("ERROR", "Failed to send")
                pass
            except Exception as e:
                print("Unidentified error:", e)

    def send_topic(self, device_id, main_payload):
        self.logger("INFO", "Transmitting message...")
        if not self.pipes_open:
            raise ValueError("Pipes must be open before sending message. Call open_pipes() first.")
        
        self.nrf.stop_listening()
        deviceId = 444555
        timestamp = utime.ticks_ms()

        sample_obj = { "device_id": 123123123, "sensor_state": "OPEN"}
        text_obj = json.dumps(sample_obj)
        print("TEXT OBJ", (text_obj))
        chunked_array = []
        # for x in range(len(text_obj)):
        for x in range(0, len(text_obj), 8):
            print("X is", x)
            chunked_array.append(text_obj[x:x + 8])
        
        self.send_chunked(chunked_array)
        print("CHUNKED", chunked_array)
        

        self.nrf.start_listening()

    # LISTEN - BASE STATION CLASSES
    def incoming_message(self):
        return self.nrf.any()
    

    def get_message(self):
        while self.nrf.any():
            buf = self.nrf.recv()
            self.logger("DEBUG", "Got raw buffer:", buf)

            # TODO: Should this be separate?
            try:
                self.logger("DEBUG", "Unpacking struct...")
            except Exception as e:
                self.logger("ERROR", "Failed to unpack struct", e)
        
        # TODO: how does this return
        pass 

        # Send ACK
        utime.sleep_ms(10)
        self.nrf.stop_listening()

        # TODO: dynamically get device id from incoming request
        device_id = 0
        try:
            self.logger("DEBUG", "Sending ACK...")
            self.nrf.send(struct.pack("ii", device_id, 0))
            self.logger("INFO", "ACK sent.")
        except OSError:
            self.logger("ERROR", "Failed to send ACK")
        except TypeError:
            self.logger("ERROR", "Failed to unpack struct")
        except Exception as e:
            self.logger("ERROR", "Encountered exception:", e)

        self.nrf.start_listening()

    def get_chunked_message(self):
        chunked_message = bytes()
        end_of_tx = False
        
        while not end_of_tx:
            if self.nrf.any():
                while self.nrf.any():
                    buf = self.nrf.recv()
                    self.logger("DEBUG", "Got raw buffer:", buf)
                    chunked_message = chunked_message + buf

                    # TODO: Should this be separate?
                    try:
                        self.logger("DEBUG", "Unpacking struct...")
                    except Exception as e:
                        self.logger("ERROR", "Failed to unpack struct", e)

        self.logger("DEBUG", "Got binary", chunked_message)
        encoded_string = binascii.b2a_base64(chunked_message)
        self.logger("DEBUG", "Got encoded string from binary", encoded_string)
        decoded_string = encoded_string.decode()
        self.logger("DEBUG", "Got decoded string from base64", decoded_string)
        return decoded_string
        
        # # TODO: how does this return
        # pass 

        # # Send ACK
        # utime.sleep_ms(10)
        # self.nrf.stop_listening()

        # # TODO: dynamically get device id from incoming request
        # device_id = 0
        # try:
        #     self.logger("DEBUG", "Sending ACK...")
        #     self.nrf.send(struct.pack("ii", device_id, 0))
        #     self.logger("INFO", "ACK sent.")
        # except OSError:
        #     self.logger("ERROR", "Failed to send ACK")
        # except TypeError:
        #     self.logger("ERROR", "Failed to unpack struct")
        # except Exception as e:
        #     self.logger("ERROR", "Encountered exception:", e)

        self.nrf.start_listening()

base_station_mode = False

if not base_station_mode:
    tx_a = b"\xe1\xf0\xf0\xf0\xf0"
    rx_a = b"\xd2\xf0\xf0\xf0\xf0"

    comm = Communicator()
    comm.set_addresses(tx_a, rx_a)
    comm.configure_pins(sck=2, mosi=7, miso=4, csn=3, ce=0)
    comm.open_pipes()

    # comm.send_message(123123, 77)
    # comm.send_topic(123123, 77)
    comm.send_message_chunked("mock_payload")
else:
    # BASE STATION MODE
    rx_a = b"\xe1\xf0\xf0\xf0\xf0"
    tx_a = b"\xd2\xf0\xf0\xf0\xf0"

    comm = Communicator()
    comm.set_addresses(tx_a, rx_a)
    comm.configure_pins(sck=2, mosi=7, miso=4, csn=3, ce=0)
    comm.open_pipes()

    while True:
        message = comm.get_chunked_message()
        print("FINAL GOT", message)
        # chunked_message = bytes()
        # end_of_message = False

        # while not end_of_message:
        #     if comm.incoming_message():
        #         chunked_message = comm.get_chunked_message()