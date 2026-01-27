import ctypes
import mmap
import math
import time

class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int32),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int32),
        ("rpms", ctypes.c_int32),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int32),
        ("pitLimiterOn", ctypes.c_int32),
        ("abs", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("autoShifterOn", ctypes.c_int32),
        ("rideHeight", ctypes.c_float * 2),
        ("turboBoost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("airDensity", ctypes.c_float),
        ("kerbVibration", ctypes.c_float),
        ("slipVibration", ctypes.c_float),
    ]  # This matches the documented AC struct layout.

def open_ac_physics():
    # The AC reference lists the shared memory name as "acpmf_physics".
    # Many examples open it with the Local\ prefix on Windows. 
    mm = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics), tagname=r"Local\acpmf_physics")
    return mm, SPageFilePhysics.from_buffer(mm)

def ffb_proxy_torque(phys, wheel_angle_rad, wheel_vel_rad_s):
    # Front loads/slip
    load_fl, load_fr = phys.wheelLoad[0], phys.wheelLoad[1]   
    slip_fl, slip_fr = phys.wheelSlip[0], phys.wheelSlip[1]   

    # crude "aligning torque" proxy (you will tune this heavily)
    sat = (load_fl * slip_fl + load_fr * slip_fr)

    # damping to kill oscillations
    damping = -0.15 * wheel_vel_rad_s

    # optional "sync" spring to keep your physical wheel near game's steerAngle
    sync = 0.10 * (phys.steerAngle - wheel_angle_rad)        

    # gains + clamp
    torque_nm = 2.0 * sat + damping + sync
    torque_nm = max(min(torque_nm, 3.0), -3.0)
    return torque_nm

_rumble_on = False

def ffb_offroad_rumble(phys):
    global _rumble_on

    RUMBLE_NM = 0.5
    RUMBLE_HZ = 35.0

    kerb = abs(float(phys.kerbVibration))
    slip = abs(float(phys.slipVibration))
    intensity = max(kerb, slip)          # 0..~1 (ish), depends on AC
    intensity = max(0.0, min(intensity, 1.0))

    ON_TH  = 0.04
    OFF_TH = 0.02

    if not _rumble_on and intensity > ON_TH:
        _rumble_on = True
    elif _rumble_on and intensity < OFF_TH:
        _rumble_on = False

    if not _rumble_on:
        return 0.0

    t = time.perf_counter()
    return (RUMBLE_NM * intensity) * math.sin(2.0 * math.pi * RUMBLE_HZ * t)

_road_lp = 0.0

def ffb_road_rumble(phys):
    global _road_lp

    # 1) speed-based baseline (0..1)
    speed = float(phys.speedKmh)
    speed_gain = max(0.0, min(speed / 80.0, 1.0))  # starts building by ~80 kph

    # 2) "roughness" proxy from acceleration magnitude (in g)
    ax, ay, az = map(float, phys.accG)
    gmag = (ax*ax + ay*ay + az*az) ** 0.5

    # high-pass-ish by subtracting a slow low-pass
    _road_lp = 0.995 * _road_lp + 0.005 * gmag
    rough = max(0.0, min(gmag - _road_lp, 1.0))

    # 3) vibration signal (pick a road-ish frequency band)
    RUMBLE_HZ = 38.0  # common "road vibration" feel is ~30-45 Hz
    RUMBLE_NM = 0.35  # start small, increase carefully

    intensity = speed_gain * (0.2 + 2.5 * rough)  # baseline + roughness
    intensity = max(0.0, min(intensity, 1.0))

    t = time.perf_counter()
    return (RUMBLE_NM * intensity) * math.sin(2.0 * math.pi * RUMBLE_HZ * t)

_slide = 0.0  # 0..1 envelope

def ffb_spinout_effect(phys, wheel_vel_rad_s):
    global _slide

    # Front slip proxy (FL, FR)
    slip_fl = abs(float(phys.wheelSlip[0]))
    slip_fr = abs(float(phys.wheelSlip[1]))
    front_slip = max(slip_fl, slip_fr)

    # Only when moving
    moving = 1.0 if float(phys.speedKmh) > 20.0 else 0.0

    # Map slip to 0..1 (tune these)
    SLIP_ON = 0.5
    SLIP_FULL = 0.80
    target = 0.0
    if moving > 0.0 and front_slip > SLIP_ON:
        target = max(0.0, min((front_slip - SLIP_ON) / (SLIP_FULL - SLIP_ON), 1.0))

    # Envelope follower (fast attack, slower release)
    a = 0.25
    r = 0.05
    if target > _slide:
        _slide = (1.0 - a) * _slide + a * target
    else:
        _slide = (1.0 - r) * _slide + r * target

    # Effects: extra damping + scrub vibe
    extra_damping = -0.8 * _slide * wheel_vel_rad_s   # Nm, tune
    SCRUB_HZ = 18.0
    SCRUB_NM = 1.0
    t = time.perf_counter()
    scrub = (SCRUB_NM * _slide) * math.sin(2.0 * math.pi * SCRUB_HZ * t)

    return extra_damping + scrub, _slide


"""
mm, phys = open_ac_physics()

last_packet = -1
while True:
    if phys.packetId != last_packet:
        last_packet = phys.packetId
        wl = list(phys.wheelLoad)   # FL, FR, RL, RR
        ws = list(phys.wheelSlip)   # FL, FR, RL, RR 
        print("steerAngle:", phys.steerAngle, "speedKmh:", phys.speedKmh, "wheelLoad:", wl, "wheelSlip:", ws)
    time.sleep(0.002)  # ~500 Hz loop
"""