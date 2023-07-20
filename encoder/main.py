import machine

# Define the pins for the rotary encoder
CLK_PIN = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
DT_PIN = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
SW_PIN = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)

# Define variables to store the state of the rotary encoder
clk_state = 0
dt_state = 0
prev_clk_state = 0
button_state = 0
prev_button_state = 0
volume_level = 0

# Define a callback function to handle the rotary encoder events
def handle_encoder(pin):
    global clk_state, dt_state, prev_clk_state, button_state, prev_button_state, volume_level

    # Read the current state of the CLK and DT pins
    clk_state = CLK_PIN.value()
    dt_state = DT_PIN.value()

    # Check for clockwise rotation
    if clk_state != prev_clk_state and clk_state == dt_state:
        print("Clockwise rotation")
        volume_level = volume_level + 1
        print("Volume level", volume_level)

    # Check for counterclockwise rotation
    if clk_state != prev_clk_state and clk_state != dt_state:
        print("Counterclockwise rotation")
        volume_level = volume_level - 1
        print("Volume level", volume_level)

    # Update the previous CLK state
    prev_clk_state = clk_state

    # Read the current state of the SW pin (push button)
    button_state = SW_PIN.value()

    # Check if the button state has changed (button press or release)
    if button_state != prev_button_state:
        if button_state == 0:
            print("Button pressed")
        else:
            print("Button released")

    # Update the previous button state
    prev_button_state = button_state

# Attach interrupts to the CLK, DT, and SW pins
CLK_PIN.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=handle_encoder)
DT_PIN.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=handle_encoder)
SW_PIN.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=handle_encoder)

while True:
    handle_encoder(1)