import moteus
import vgamepad as vg
import asyncio

async def main():
    # Setup virtual gamepad and moteus
    gamepad = vg.VX360Gamepad()
    c = moteus.Controller()

    while True:
        # 1. Get motor state
        state = await c.set_stop(query=True)
        motor_pos = state.values[moteus.Register.POSITION]

        # 2. Map position to XInput Stick (Example: 1 rev = full stick range)
        # Assuming motor_pos is 0.0 to 1.0
        stick_val = int((motor_pos * 65535) - 32768)
        stick_val = max(-32768, min(32767, stick_val))

        # 3. Update the virtual Xbox controller
        gamepad.left_joystick(x_value=stick_val, y_value=0)
        gamepad.update()
        
        await asyncio.sleep(0.01) # 100Hz update rate
