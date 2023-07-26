import wifimgr
import gc
import os

gc.enable()
print(gc.mem_alloc())
print(gc.mem_free())
# free()
print("HELLO")
wifimgr.force_disconnection()
wlan = wifimgr.get_connection()
print("WLAN IS", wlan)
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D


# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")