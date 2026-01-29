import serial


def read_pedal_degrees(port: str = "COM4", baud: int = 115200, timeout_s: float = 1.0):
    """
    Read a single sample containing two angles (degrees) from an Arduino over serial.

    Expected Arduino output format (one line):
      angle1,angle2
    Example:
      123.4,278.56

    Returns:
      (float, float): (angle1_deg, angle2_deg)
      None: on timeout / blank line / parse error
    """
    with serial.Serial(port, baud, timeout=timeout_s) as ser:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            return None

        try:
            a_str, b_str = line.split(",", 1)
            return float(a_str), float(b_str)
        except ValueError:
            return None
