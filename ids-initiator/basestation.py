class BaseStation:
    def __init__(self):
        self.on = True
        self.devices = []
    

    def register_device(self, d_id):
        self.devices.append(d_id)

    def process_topic(self, payload):
        print("DEBUG", "Processing topic...")
        # self.devices.

    # # Main loop here
    # while True:
    #     pass