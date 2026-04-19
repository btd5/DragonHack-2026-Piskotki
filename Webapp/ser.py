import serial
import time

with serial.Serial('COM11', 9600, timeout=1) as ser:
    ser.write(b'1')
    time.sleep(10)