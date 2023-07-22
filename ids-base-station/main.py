import time
# import zigbee

# # Create a Zigbee object
# zigbee = zigbee.Zigbee()

# # Set the address of the sensor
# address = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]

# # Open the receiving pipe
# zigbee.openReadingPipe(1, address)

# # Start listening
# zigbee.startListening()

# # Main loop
# while True:
#     # Check if there is a message
#     if zigbee.available():
#         # Read the message
#         message = zigbee.read()

#         # Print the message
#         print("Message: " + message)

#         # Acknowledge the message
#         zigbee.write([1])

#         # Wait for a second
#         time.sleep(1)
