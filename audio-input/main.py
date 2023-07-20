import machine
from machine import I2C, Pin
import utime
# from pico_i2c_lcd import I2cLcd
# import sys
# sys.path.append('./ssd1306.py')
# from ./ssd1306.py import ssd1306
# import wave

# for audio recording
import rp2
# import audiobusio
import array
import uos

# for audio pin
# adc = machine.ADC(26)
adc = machine.ADC(26)
# adc.atten(machine.ADC.ATTN_11DB)

# audio parameters
a_threshold = 2000
sample_rate = 8000
record_duration = 10
filename = "./recordin.wav"

# detect input state
def detect_input_start():
    print("Checking for input")
    while True:
        # sample = adc.read()
        sample = adc.read_u16()
        print("Checking")
        print("GOT SAMPLE", sample)
        utime.sleep(0.2)
        # if sample > a_threshold:
            # break

print("Program stood up")
detect_input_start()