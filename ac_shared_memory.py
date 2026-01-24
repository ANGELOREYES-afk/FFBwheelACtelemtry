import ctypes
import mmap
import time
import math

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


mm, phys = open_ac_physics()

last_packet = -1
while True:
    if phys.packetId != last_packet:
        last_packet = phys.packetId
        wl = list(phys.wheelLoad)   # FL, FR, RL, RR
        ws = list(phys.wheelSlip)   # FL, FR, RL, RR 
        print("steerAngle:", phys.steerAngle, "speedKmh:", phys.speedKmh, "wheelLoad:", wl, "wheelSlip:", ws)
        # --Put moteus commands here--
    time.sleep(0.002)  # ~500 Hz loop