import machine
from machine import I2C, Pin
import utime
import time
# import ssd1306
from ssd1306 import SSD1306_I2C
from lynx import Lynx
import requests
import json
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
# KEYPAD SETUP
# This is the setup without I2C
#
keypad = [
    ["D", "C", "B", "A"],
    ["#", 9, 6, 3],
    [0, 8, 5, 2],
    ["*", 7, 4, 1]
]
keypadRows = [8, 9, 10, 11]
keypadCols = [12, 13, 14, 15]
rowPins = []
colPins = []

key_press = ""

for x in range(0,4):
    rowPins.append(Pin(keypadRows[x], Pin.OUT))
    rowPins[x].value(1)
    colPins.append(Pin(keypadCols[x], Pin.IN, Pin.PULL_DOWN))
    colPins[x].value(0)

def scankeys():  
    global key_press
    for row in range(4):
        for col in range(4):
            rowPins[row].high()
            key = None
            
            if colPins[col].value() == 1:
                print("You have pressed:", keypad[row][col])
                key_press = keypad[row][col]
                utime.sleep(0.3)
                    
        rowPins[row].low()


# Define I2C pins
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)  # Adjust the pin numbers accordingly

utime.sleep(0.1)
print("AWAKE")
# getting I2C address
I2C_ADDR = i2c.scan()[0]
print("I2C addres", I2C_ADDR)

oled = SSD1306_I2C(128, 64, i2c)


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
        'displayName': 'Debug Mode',
        'savedOption': 0,
        'optionsList': [False, True],
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

#
# SECURITY GLOBALS
# 
systemArmed = False
systemTriggered = False
shouldArm = False
shouldTrigger = False
armTimeout = 0
passcode = "1111"
passcodeDigitLength = 4
# tempPasscode = ""

def shouldArmAlarm():
    global armTimeout, shouldArm, systemArmed
    shouldArm = False
    renderBasicMessage("ARMING", "Will arm in", "9 seconds")
    for x in range(armTimeout):
        renderBasicMessage("ARMING", "Will arm in", str(armTimeout - x))
        print("A second")
        utime.sleep(1)
    systemArmed = True
    renderBasicMessage("SYSTEM ARMED", "ONLINE", "Watch")
    print("INFO: System armed")


def toggleTriggerWorkflow():
    global shouldTrigger, systemTriggered, passcodeDigitLength
    shouldTrigger = False
    systemTriggered = True
    oled.invert(1)
    renderBasicMessage("** ALARM **", "Triggered", "Enter Code")
    utime.sleep(0.5)
    # getPasscodeInput()

    resolveAlarm("* ALARM ACTIVE *")


def resolveAlarm(message):
    global passcode, systemTriggered, systemArmed
    errorTime = ""
    while systemTriggered or systemArmed:
        response = getPasscodeInput(message, errorTime)
        if response == passcode:
            # IF PASSCODE CORRECT, deaactive all alarms
            systemTriggered = False
            systemArmed = False
            renderHomeScreen()
            print("INFO: Alarm deactived")
        # PASSCODE INCORRECT
        else:
            # Retry alarm
            print("INFO: Alarm not deactivated, still in alarm sate")
            errorTime = utime.time()
            print("Error time set to", errorTime)
            renderErrorMessageOverlay("Incorrect")


def toggleDisarmWorkflow():
    print("INFO: Disarm workflow toggle")
    resolveAlarm("**** DISARM ****")


def getPasscodeInput(title, errorTime):
    global passcode, key_press, passcodeDigitLength
    renderBasicMessage(title, "Enter Code", ">:")
    tempPasscode = ""
    

    def generateStars(numbs):
        stringer = ""
        for x in range(numbs):
            stringer = stringer + "*"
        return stringer
    

    while True:
        # display error message
        if errorTime != "":
            currentTime = utime.time()
            elapsedTime = currentTime - errorTime
            print("CURR TIME", currentTime, "ELP", elapsedTime)
            timeoutPeriod = 2
            if elapsedTime > timeoutPeriod:
                print("errorDone")
                errorTime = ""

        scankeys()
        # if enter button pressed
        if key_press == "#":
            key_press = ""
            return tempPasscode
        # add key presses to temp password
        if key_press != "":
            tempPasscode = tempPasscode + str(key_press)
            print("Passcode is now", tempPasscode)
            oled.text(generateStars(len(tempPasscode)), 15, 32)
            oled.show()
            key_press = ""
        # reset temp password if # or too many digits
        if key_press == "*" or len(tempPasscode) > passcodeDigitLength:
            key_press = ""
            tempPasscode = ""
        # debounce
        utime.sleep(0.05)


#
# LOADING AND SCREEN RENDERING
#

print("Waiting for button press...")

def startLoadingFeedback():
    print("LED started")
    shouldToggleLED = True
    statusLed.on()


def endLoadingFeedback():
    shouldToggleLED = False
    statusLed.off()


def renderErrorMessageOverlay(message):
    oled.text(message, 0, 50, 1)
    oled.show()


def renderBasicMessage(title, line1, line2):
    oled.fill(0)
    oled.text(title, 0, 5)
    oled.text(line1, 0, 18)
    oled.text(line2, 0, 30)
    oled.show()


def renderScreenMessage(title, line1, line2):
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(line1, 0, 16)
    oled.hline(0, 25, 128, 1)
    oled.text(line2, 0, 27)
    # test = Lyn
    # tester = Lynx(oled)
    Lynx(oled).renderEnterArrow(0, 45)
    oled.text("Select", 15, 45)
    Lynx(oled).renderScrollArrow(0, 55)
    oled.text("Scroll", 15, 55)
    oled.show()
    print("Finished rendering screen")
    endLoadingFeedback()


def renderHomeScreen():
    oled.invert(False)
    onlineStatus = "     Online" if menuOptions[0]['savedOption'] == 1 else "    Offline"
    # lcd.putstr(onlineStatus)
    displayHomeScreenMessage("DHARMA SECURITY", "GL-10 Controller", onlineStatus)
    endLoadingFeedback()

def displayHomeScreenMessage(title, line1, line2):
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(line1, 0, 16)
    oled.text(line2, 0, 27, 2)
    Lynx(oled).renderEnterArrow(30, 45)
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


def displayFullScreenMessage(title, message):
    oled.fill(0)
    oled.text(title, 0, 0)
    oled.text(message, 0, 30)
    oled.show()
    utime.sleep(0.75)

# WELCOME SCREEN MESSAGE
# renderWelcomeScreen()
# utime.sleep(3)
renderHomeScreen()

# print(time.now())

def writeLogMessage():
    file = open("log.txt", "a")
    currTime = time.time()
    file.write("\n%s,Motion,Section 7"%(currTime))
    # time = utime.time()
    # file.write("TIME IS", "str(time)")
    file.close
    file2 = open("log.txt")
    print("READING FILE BELOW:")
    print(file2.read())
    file2.close


def handleMotion():
    print("Motion detected")
    if not systemArmed:
        displayFullScreenMessage("Motion Detected", "Living Room")
        writeLogMessage()
        
        renderHomeScreen()


# API CALL
def makeApiCall():
    url = "https://e25n1uqc6c.execute-api.us-east-1.amazonaws.com/default/handleEvent"

    payload = json.dumps({
    "deviceId": 123123,
    "userId": 234234234,
    "homeId": 34534345,
    "eventType": "MOTION",
    "eventValue": "DOOR",
    "sensorValue": "OPEN"
    })
    
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


# LED
# blink_interval = 0.3  # Blink interval in seconds
# previous_time = utime.ticks_ms()

#############
# MAIN LOOP # 
#############
while True:
    # ARM SYSTEM
    if key_press == "A" and not systemArmed:
        print("INFO: Alarm arm signal from button press")
        key_press = ""
        shouldArmAlarm()

    # TRIGGER ALARM: A
    if key_press == "A" and systemArmed:
        print("INFO: Alarm trigged from button press")
        key_press = ""
        toggleTriggerWorkflow()
    
    # DISARM SYSTEM:
    if key_press == "D":
        key_press = ""
        toggleDisarmWorkflow()

    # HANDLE MOTION
    if key_press == 1 and not menuMode:
        key_press = ""
        handleMotion()

    # SHOULD RENDER MENU - logic to determine menu level and render content
    if shouldRenderMenu:
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
    # if menuButton.value() == 1:
    if key_press == "#":
        key_press = ""
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
            displayFullScreenMessage("MENU", "     Saved!")
            renderHomeScreen()

        while menuButton.value() == 1:
            pass  # Wait for button release

    # SCROLL DOWN BUTTON
    # if scrollButton.value() == 1:
    if key_press == "C":
        key_press = ""
        print("Button SCROLL DOWN pressed!")
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

    # SCROLL UP BUTTON
    # if scrollButton.value() == 1:
    if key_press == "B":
        key_press = ""
        print("Button SCROLL UP pressed!")
        startLoadingFeedback()
        if menuMode and not subMenuMode:
            # if menuPage == len(menuOptions) - 1:
            if menuPage == 0:
                menuPage = len(menuOptions) - 1
            else:
                menuPage = menuPage - 1
        if menuMode and subMenuMode:
            # if subMenuPage == len(menuOptions[menuPage]['optionsList']) - 1:
            if subMenuPage == 0:
                subMenuPage = len(menuOptions[menuPage]['optionsList']) - 1
            else:
                subMenuPage = subMenuPage - 1
        if menuMode:
            shouldRenderMenu = True
        while scrollButton.value() == 1:
            pass  # Wait for button release

    # CLEAR BUTTON
    # if clearButton.value() == 1:
    if key_press == "*":
        key_press = ""
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


    # scan for keypad input
    scankeys()
    # small delay to prevent excessive CPU usage
    utime.sleep(0.01)