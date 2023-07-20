import machine
from machine import I2C, Pin
import utime
# import ssd1306
from ssd1306 import SSD1306_I2C

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
# oled = ssd1306(128, 64, i2c)

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
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(line1, 0, 16)
    oled.hline(0, 25, 128, 1)
    oled.text(line2, 0, 27)
    renderEnterArrow(0, 45)
    oled.text("Select", 15, 45)
    renderScrollArrow(0, 55)
    oled.text("Scroll", 15, 55)
    oled.show()
    print("Finished rendering screen")
    endLoadingFeedback()


def renderEnterArrow(x, y):
    line1 = [x, y, x, y + 3] 
    line2 = [x, y + 3, x + 7, y + 3]
    line3 = [x + 4, y, x + 7, y + 3]
    line4 = [x + 4, y + 6, x + 7, y + 3]
    oled.line(line1[0], line1[1], line1[2], line1[3], 1)
    oled.line(line2[0], line2[1], line2[2], line2[3], 1)
    oled.line(line3[0], line3[1], line3[2], line3[3], 1)
    oled.line(line4[0], line4[1], line4[2], line4[3], 1)


def renderScrollArrow(x, y):
    line1 = [x + 3, y, x + 3, y + 7]
    line2 = [x, y + 4, x + 3, y + 7]
    line3 = [x + 7, y + 4, x + 3, y + 7]
    oled.line(line1[0], line1[1], line1[2], line1[3], 1)
    oled.line(line2[0], line2[1], line2[2], line2[3], 1)
    oled.line(line3[0], line3[1], line3[2], line3[3], 1)

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
    displayHomeScreenMessage("B:100% Tx Rx", "GL-10 Controller", onlineStatus)
    endLoadingFeedback()

def displayHomeScreenMessage(title, line1, line2):
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(line1, 0, 16)
    oled.text(line2, 0, 27)
    renderEnterArrow(30, 45)
    # renderScrollArrow(0, 45)
    oled.text("Menu", 45, 45)
    oled.show()
    print("Finished rendering screen")
    endLoadingFeedback()


def renderWelcomeScreen():
    oled.invert(True)
    oled.text("Grayrock Labs", 12, 5, 1)
    oled.text("GL-10", 46, 20, 1)
    oled.text("Repeater", 35, 35, 1)
    oled.text("Controller", 30, 45, 1)
    oled.text("v 1.0.1", 38, 55, 1)
    oled.show()

# WELCOME SCREEN MESSAGE
# renderWelcomeScreen()
# utime.sleep(3)
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
            # renderScreenMessage("MENU", "++ MENU ++ %s/%s" % (menuPage + 1, len(menuOptions)), menuOptions[menuPage]['displayName'])
            renderScreenMessage("MENU", "Page %s/%s" % (menuPage + 1, len(menuOptions)), menuOptions[menuPage]['displayName'])
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
        # SAVE OPTION
        elif menuMode and subMenuMode:
            menuOptions[menuPage]['savedOption'] = subMenuPage
            menuMode = False
            subMenuMode = False
            oled.fill(0)
            oled.text("MENU", 0, 0)
            oled.text("Saved!", 35, 30)
            oled.show()
            utime.sleep(0.75)
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
        if menuMode:
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