import machine
from machine import I2C, Pin
import utime
import math
from ssd1306 import SSD1306_I2C
import freesans20
import roboto16
import roboto20
import roboto28
import writer

# DEFINE GLOBALS
PAGE_TIMEOUT = 3000
FETCH_INTERVAL = 10000
FETCH_TIME = 0 # immediately fetch on load
HUMIDITY_TIMEOUT = 6000
HUMIDITY_TIME = utime.ticks_ms()

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

# END OF KEYPAD SETUP

#
# I2C - OLED DISPLAY
#

# Define I2C pins
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)  # Adjust the pin numbers accordingly

utime.sleep(0.1)
print("AWAKE")
# getting I2C address
I2C_ADDR = i2c.scan()[0]
print("I2C addres", I2C_ADDR)

oled = SSD1306_I2C(128, 64, i2c)

# END OF I2C DISPLAY SETUP

#
# DISPLAY PAGES
#

displayPageList = [
    {
        "displayName": "Temperature (In)",
        "value": "70.4",
        "unit": "F",
        "location": "Inside"
    },
    {
        "displayName": "Humidity",
        "value": "54",
        "unit": "%",
        "location": "Inside"
    },
    {
        "displayName": "Temperature (Out)",
        "value": "70.4",
        "unit": "F",
        "location": "Inside"
    },
    {
        "displayName": "Pressure",
        "value": "304",
        "unit": "hPa",
        "location": "Outside"
    },
    {
        "displayName": "UV Index",
        "value": "4",
        "unit": "of 10",
        "location": "Outside"
    },
    {
        "displayName": "Altitude",
        "value": "835",
        "unit": "ft",
        "location": "Outside"
    }
]

def renderBasicMessage(title, line1, line2):
    oled.fill(0)
    oled.text(title, 0, 5)
    oled.text(line1, 0, 18)
    oled.text(line2, 0, 30, 3)
    oled.show()

renderBasicMessage("Weather", "State", "North")


def renderDisplayPage():
    print("rendering display page", page_display)
    oled.fill(0)

    formattedUnit = displayPageList[page_display]['value'] + " " + displayPageList[page_display]['unit'] 
    renderCustomFont(roboto28, formattedUnit, 5, 20)
    renderCustomFont(roboto16, displayPageList[page_display]['displayName'], 5, 00)

    oled.show()

def renderCustomFont(font, text, x, y):
    fontWriter = writer.Writer(oled, font)
    fontWriter.set_textpos(x, y)
    fontWriter.printstring(str(text))

# Display Help Message
def displayHelpMessage(value):
    if value < 30:
        return "Dry"
    elif value < 60:
        return "Normal"
    elif value < 65:
        return "Spooky"
    else:
        return "Humid"

page_time = utime.ticks_ms()
page_display = 0
renderDisplayPage()


#
# WEATHER
#

# SAVE HUMIDITY VALUES
humidityValues = []
def saveHumidity(value):
    newValue = {
        "humidity": value,
        "timestamp": utime.time()
    }
    humidityValues.append(newValue)

# CHECK HUMIDITY TREND
WINDOW_SIZE = 2
data = [
    {"value": "10.6"},
    {"value": "11.2"},
    {"value": "9.8"},
    {"value": "12.1"},
    {"value": "15.7"},
    {"value": "14.7"},
    {"value": "13.7"},
    {"value": "12.7"},
    {"value": "11.7"},
    {"value": "10.4"}
]
def checkTrend():
    # TODO: Temp, convert to feed into func
    objArray = data
    # objArray = humidityValues

    # Optional: convert all to floats
    valueList = [float(obj["value"]) for obj in objArray]
    trends = []

    print("A window", valueList[4:8])

    # convert all values to flots
    # for x in range(WINDOW_SIZE, len(valueList)):
    iterationsLength = math.ceil(len(valueList) / WINDOW_SIZE)
    for x in range(iterationsLength):
        # window = valueList[x - WINDOW_SIZE:x]
        currStart = x * WINDOW_SIZE
        window = valueList[currStart:currStart + WINDOW_SIZE]
        print("WINDOW", window)
        trend = None

        if all(window[j] < window[j + 1] for j in range(len(window) - 1)):
            trend = "increasing"
        elif all(window[j] > window[j + 1] for j in range(len(window) - 1)):
            trend = "decreasing"

        trends.append(trend)
    
    print("TRENDS ARE", trends)

# checkTrend()

while True:
    # create timer to iterate though pages
    currTime = utime.ticks_ms()

    # change display to next page after timout
    if utime.ticks_diff(currTime, page_time) > PAGE_TIMEOUT:
        print("Existing Page", page_display)
        page_time = utime.ticks_ms()
        page_display = page_display + 1 if page_display < len(displayPageList) - 1 else 0
        print("New Page", page_display)
        renderDisplayPage()
        saveHumidity(utime.ticks_ms())
        print("HUMI VALUES", humidityValues)
    
    # fetch values on FETCH_INTERVAL
    if utime.ticks_diff(currTime, FETCH_TIME) > FETCH_INTERVAL:
        FETCH_TIME = utime.ticks_ms()
        print("Fetching values...")

    # save values at SAVE_INTERVAL
    if utime.ticks_diff(currTime, HUMIDITY_TIME) > HUMIDITY_TIMEOUT:
        HUMIDITY_TIME = utime.ticks_ms()
        # checkTrend()



    # small delay to save CPU usage
    utime.sleep(0.01)