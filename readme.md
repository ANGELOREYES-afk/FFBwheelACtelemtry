# Mini Haptic Steering Wheel Controller | TAMUHACK 2026

Created With Moteus, vgamepad, stm32, as5600 magnet sensors, and Assetto Corsa Telemetry Tools

Mini steering wheel controller with haptic feedback capabilities, with controller support and in-game integration.

## Things To Do:
- [x] Calibrate Moteus Motor
- [x] Program Moteus controls
- [x] Obtain Force Feedback Data
- [x] Link Moteus Controls to Gameplay
- [x] Finish Moteus Mount
- [x] Finalize Pedal design
- [x] Obtain magent angle data
- [x] Link Magnet Data to Gameplay
## Installation
REQUIRED DEPENDENCIES!

**AS5600**\
https://github.com/RobTillaart/AS5600

**VGAMEPAD**\
https://github.com/yannbouteiller/vgamepad

**ViGEmBus** *only if not installed with vgamepad*\
https://github.com/nefarius/ViGEmBus

**MOTEUS**\
https://pypi.org/project/moteus

After downloading dependencies, run `motor.py` while Assetto Corsa or other racing game is running. \
**MAKE SURE MOTEUS MOTOR IS CALIBRATED BEFORE USE**

From there, the wheel should be good to go. Feel free to alter any torque/rotation values within `motor.py` and `ac_shared_memory.py`

Run `stopMoteus.py` to reset the moteus motor


## Usage
Use in Assetto Corsa or any other racing game that supports xbox controllers, only Assetto Corsa supports haptic feedback