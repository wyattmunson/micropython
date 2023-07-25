import struct
import utime
import json
from machine import Pin, SPI
from nrf24l01 import NRF24L01

class Communicator:
    def __init__(self):
        self.addresses_are_set = False
        self.pins_configured = False
        self.pipes_open = False
        self.log_level = 5
        # TODO: get if sensor/base station, handle tx pipes accordingly

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

        # TODO: Provide handling for different address formats

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

    
    def send_json_message(self, json_payload):
        if not self.pipes_open:
            raise ValueError("Pipes must be open before sending message. Call open_pipes() first.")
        
        self.logger("INFO", "Transmitting message with chunks...")
        self.nrf.stop_listening()
        # TODO: Get device id from class or parent class
        deviceId = 444555
        # TODO: add timestamp + server timestamp? 
        timestamp = utime.ticks_ms()

        encoded = json.dumps(json_payload).encode("utf-8")
        chunks = []
        chunk_size = 5

        for i in range(0, len(encoded), chunk_size):
            chunks.append(encoded[i:i + chunk_size])
        
        for chunk in chunks:
            print(chunk)

        # add newline as tx termination charachter
        # TODO: pack into last chunk if space exists
        chunks.append(b"\n")

        self.logger("INFO", "Transmitting message in %i chunks..." % (len(chunks)))

        for index, chunk in enumerate(chunks):
            try:
                self.logger("DEBUG", "Sending chunk %i..." % (index))
                self.nrf.send(chunk)
                self.logger("INFO", "Message transmitted successfully")
            except OSError as e:
                self.logger("ERROR", "Failed to send. Upstream error:", e)
                pass
            except Exception as e:
                print("Unidentified error:", e)

        # TODO: Listen for ACK request from base station 

        # TODO: do not restart rx pipe on sensors
        # TODO: manage device type (sensor/base station)
        self.nrf.start_listening()


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
                    # chunked_message = chunked_message + buf
                    
                    # New line triggers end of message - only item in message
                    if b"\n" in buf:
                        self.logger("DEBUG", "New line seen")
                        end_of_tx = True
                    else:
                        index = buf.find(b"\x00")
                        chunked_message = chunked_message + buf[:index]

        self.logger("DEBUG", "Received message:", chunked_message)

        self.nrf.start_listening()
        
        return chunked_message.decode()


#########################
# DEVELOPMENT MODE ONLY #
#########################

base_station_mode = False

if not base_station_mode:
    tx_a = b"\xe1\xf0\xf0\xf0\xf0"
    rx_a = b"\xd2\xf0\xf0\xf0\xf0"

    comm = Communicator()
    comm.set_addresses(tx_a, rx_a)
    comm.configure_pins(sck=2, mosi=7, miso=4, csn=3, ce=0)
    comm.open_pipes()

    # comm.send_topic(123123, 77)
    comm.send_json_message({"d_id":1234567, "sensor": "OPEN"})

    payload = {'test': 4, "another_message": "this is is a very long message that may have issues", "fake": False, "another_var": "HERE IS A VERY LONG STRING"}

    print(len(payload))
    # for x in range(payload)
    
    encoded_payload = json.dumps(payload).encode()
    print("ENCODED PAYLOAD", encoded_payload, type(encoded_payload))
    portion = encoded_payload[:8]
    print("PORTION", portion, len(portion))

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
