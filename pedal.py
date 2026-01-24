# Pedal data & numbers here!!!!
# Read from Arduino serial -> controller input

import serial

PORT = "COM4"          # Windows example; mac/linux often like /dev/ttyACM0 or /dev/tty.usbmodemXXXX
BAUD = 115200

with serial.Serial(PORT, BAUD, timeout=1) as ser:  # pySerial Serial() takes baudrate like 115200 [web:3]
    while True:
        line = ser.readline().decode("utf-8", errors="replace").strip()  # readline reads until EOL/newline [web:6]
        if not line:
            continue

        try:
            deg_s = line
            deg = float(deg_s)
            print(deg)   # now you can log/plot/use these values
        except ValueError:
            # If a non-CSV line arrives (e.g., debug prints), handle it here
            print("Unparsed:", line)
