import serial


def read_pedal_degrees(port: str = "COM4", baud: int = 115200, timeout_s: float = 1.0):
    """
    Read a single AS5600 angle sample (in degrees) from an Arduino over serial.

    Expected Arduino output format (one value per line):
      123.45

    Returns:
      float: degrees (0..360-ish depending on your firmware)
      None:  on timeout / blank line / parse error
    """
    with serial.Serial(port, baud, timeout=timeout_s) as ser:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            return None
        try:
            return float(line)
        except ValueError:
            return None
