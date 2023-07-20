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
# adc = machine.ADC(machine.Pin(34))
# adc.atten(machine.ADC.ATTN_11DB)


# for status LED
STATUS_LED_PIN = 12
statusLed = Pin(STATUS_LED_PIN, Pin.OUT)
shouldToggleLED = False

######### START SSD
# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

from micropython import const
import framebuf


# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time

        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

######### END SSD 

#
# I2C SETUP
#

# Define I2C pins
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)  # Adjust the pin numbers accordingly

utime.sleep(0.1)
print("AWAKE")
# getting I2C address
I2C_ADDR = i2c.scan()[0]
print("I2C addres", I2C_ADDR)

# creating an LCD object using the I2C address and specifying number of rows and columns in the LCD
# LCD number of rows = 2, number of columns = 16
# lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
# oled = ssd1306.SSD1306_I2C(128, 32, i2c)
oled = SSD1306_I2C(128, 64, i2c)

#
# AUDIO
#
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
ADC_PIN = 26
adc = machine.ADC(machine.Pin(ADC_PIN))
# adc.atten(machine.ADC.ATTN_11DB)
# adc.width(machine.ADC.WIDTH_12BIT)

#
# MENU OPTIONS
#
menuButton = machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_DOWN)
scrollButton = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_DOWN)
clearButton = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_DOWN)

menuMode = False
subMenuMode = False
shouldRenderMenu = False
menuPage = 0
subMenuPage = 0
menuOptions = [
    {
        'displayName': 'Wake Mode',
        'savedOption': 1,
        'optionsList': [False, True],
        'optionsList2': [True, False],
        'type': 'boolean'
    },
    {
        'displayName': 'Record Volume',
        'savedOption': 5,
        'optionsList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'optionsList2': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'type': 'numeric'
    },
    {
        'displayName': 'Playback Volume',
        'savedOption': 5,
        'optionsList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'optionsList2': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'type': 'numeric'
    },
    {
        'displayName': 'Delay after PTT',
        'savedOption': 0,
        'optionsList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'optionsList2': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'type': 'numeric'
    },
    {
        'displayName': 'Delay playback',
        'savedOption': 0,
        'optionsList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'optionsList2': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'type': 'numeric'
    },
    {
        'displayName': 'Roger Beep',
        'savedOption': 0,
        'optionsList': [False, True],
        'optionsList2': [True, False],
        'type': 'boolean'
    }
]

print("Waiting for button press...")

def startLoadingFeedback():
    print("LED started")
    shouldToggleLED = True
    statusLed.on()


def endLoadingFeedback():
    shouldToggleLED = False
    statusLed.off()


def renderScreenMessage(title, line1, line2):
    # lcd.clear()
    # lcd.putstr(line1)
    # lcd.move_to(0,1)
    # lcd.putstr(line2)
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(line1, 0, 16)
    oled.text(line2, 0, 26)
    oled.show()
    print("Finished rendering screen")
    endLoadingFeedback()


def renderHomeScreen():
    # oled.clear()
    # This does work below, but unneeded as renders twice
    # oled.fill(0)
    # oled.text("B:100%  Tx Rx", 0, 0)
    # oled.text("Online", 0, 10)
    # oled.show()
    
    
    # lcd.clear()
    # lcd.putstr("GL-10 Controller")
    # lcd.move_to(0,1)
    oled.invert(False)
    onlineStatus = "     Online" if menuOptions[0]['savedOption'] == 1 else "    Offline"
    # lcd.putstr(onlineStatus)
    renderScreenMessage("B:100% Tx Rx", "GL-10 Controller", onlineStatus)
    endLoadingFeedback()

def renderWelcomeScreen():
    oled.invert(True)
    oled.text("Grayrock Labs", 12, 5, 1)
    oled.text("GL-10", 46, 20, 1)
    oled.text("Repeater", 35, 35, 1)
    oled.text("Controller", 30, 45, 1)
    oled.text("v 1.0.1", 38, 55, 1)
    oled.show()


renderWelcomeScreen()
utime.sleep(3)
renderHomeScreen()




# LED
# blink_interval = 0.3  # Blink interval in seconds
# previous_time = utime.ticks_ms()

while True:
    # currentTime = utime.ticks_ms()
    # if utime.ticks_diff(currentTime, previous_time) >= blink_interval * 1000:
    #     print("TICK")
    #     if shouldToggleLED:
    #         print("Should toggle LED")
    #         statusLed.toggle()  # Toggle the LED state
    #     previous_time = currentTime

    if shouldRenderMenu:
        # lcd.clear()
        if subMenuMode:
            secondLine = ""
            # If currently selected, mark
            if menuOptions[menuPage]['savedOption'] == subMenuPage:
                secondLine = "[*]"
            else:
                secondLine = "[ ]"
            # If its true/false display those optins
            if menuOptions[menuPage]['type'] == "boolean":
                if menuOptions[menuPage]['optionsList'][subMenuPage] == True:
                    secondLine = secondLine + " True"
                else:
                    secondLine = secondLine + " Flase"
            else: 
                secondLine = secondLine + " " + str(menuOptions[menuPage]['optionsList'][subMenuPage])
            renderScreenMessage("MENU", "> %s " % (menuOptions[menuPage]['displayName']), secondLine)
        else:
            renderScreenMessage("MENU", "++ MENU ++ %s/%s" % (menuPage + 1, len(menuOptions)), menuOptions[menuPage]['displayName'])
        shouldRenderMenu = False

    # ENTER BUTTON
    if menuButton.value() == 1:
        print("Button ENTER pressed!")
        startLoadingFeedback()
        if not menuMode:
            menuMode = True
            shouldRenderMenu = True
        elif menuMode and not subMenuMode:
            subMenuPage = menuOptions[menuPage]['savedOption']
            subMenuMode = True
            shouldRenderMenu = True
        elif menuMode and subMenuMode:
            menuOptions[menuPage]['savedOption'] = subMenuPage
            menuMode = False
            subMenuMode = False
            renderHomeScreen()

        while menuButton.value() == 1:
            pass  # Wait for button release

    # SCROLL BUTTON
    if scrollButton.value() == 1:
        print("Button SCROLL pressed!")
        startLoadingFeedback()
        if menuMode and not subMenuMode:
            if menuPage == len(menuOptions) - 1:
                menuPage = 0
            else:
                menuPage = menuPage + 1
        if menuMode and subMenuMode:
            if subMenuPage == len(menuOptions[menuPage]['optionsList']) - 1:
                subMenuPage = 0
            else:
                subMenuPage = subMenuPage + 1
        shouldRenderMenu = True
        while scrollButton.value() == 1:
            pass  # Wait for button release

    # CLEAR BUTTON
    if clearButton.value() == 1:
        print("Button CLEAR pressed!")
        startLoadingFeedback()
        if menuMode and not subMenuMode:
            menuMode = False
            renderHomeScreen()
        elif menuMode and subMenuMode:
            subMenuMode = False
            shouldRenderMenu = True
        while clearButton.value() == 1:
            pass  # Wait for button release

    # small delay to prevent excessive CPU usage
    utime.sleep(0.01)