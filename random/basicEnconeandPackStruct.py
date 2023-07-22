import struct
import json

def pack_payload(payload):
  device_id = struct.pack('<I', payload['deviceId'])
  action = payload['action'].encode('utf-8')
  another_var = payload['anotherVar'].encode('utf-8')
  struct_size = struct.calcsize('<I') + len(action) + len(another_var)
  byte_array = bytearray(struct_size)
  struct.pack_into('<I', byte_array, 0, payload['deviceId'])
  struct.pack_into('{}s'.format(len(action)), byte_array, 4, action)
  struct.pack_into('{}s'.format(len(another_var)), byte_array, 4 + len(action), another_var)
  buffer = memoryview(byte_array)
  return struct_size, buffer

if __name__ == '__main__':
  payload = {"deviceId": 123123123, "action": "SOME THING", "anotherVar": "A much larger string"}
  struct_size, buffer = pack_payload(payload)
  print(struct_size)
  print(buffer)