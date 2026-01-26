import asyncio
import math

import moteus
import vgamepad as vg
import ac_shared_memory as ac

def clamp(x, lo, hi):
    """
    Prevents x values from goes below and above certain values
    
    :param x: x value
    :param lo: lower bound
    :param hi: high bound
    """
    return lo if x < lo else hi if x > hi else x

async def main():
    gamepad = vg.VX360Gamepad()  # virtual Xbox360 pad 
    c = moteus.Controller()      # set id=... if needed 

    mm, phys = ac.open_ac_physics()  # AC shared memory 

    # Tune these in moteus config itself, -> moteus_gui.tview
    MAX_TORQUE = 2.0            # start low for safety 
    KP_SCALE = 1              # stiffness scaling in position mode 
    KD_SCALE = 1              # damping scaling in position mode 
    STEER_RANGE_ROT = 1.25      # rotations lock-to-lock/2 (example); tune to your wheel
    ROTATION_SCALE = 4.0        # rotation scale factor; tune to your wheel


    try:
        st0 = await c.query()
        zero_pos = float(st0.values[moteus.Register.POSITION])
        while True:
            # 1) Read moteus state WITHOUT stopping the motor
            st = await c.query()  
            raw_pos = float(st.values[moteus.Register.POSITION])
            raw_vel = float(st.values[moteus.Register.VELOCITY])
            motor_pos_rot = (raw_pos - zero_pos - ROTATION_SCALE) * ROTATION_SCALE  # rotations output shaft 
            motor_vel_hz  = raw_vel   # Hz output shaft 
            print("Motor pos: " + str(motor_pos_rot) + " Motor Vel: " + str(motor_vel_hz))

            # 2) Build FFB torque from AC + motor state
            # Your ffb_proxy_torque expects radians; convert rotations -> radians.
            motor_pos_rad = motor_pos_rot * 2.0 * math.pi
            motor_vel_rad_s = motor_vel_hz * 2.0 * math.pi
            

            torque_nm = ac.ffb_proxy_torque(phys, motor_pos_rad, motor_vel_rad_s)  
            torque_nm = clamp(torque_nm, -MAX_TORQUE, MAX_TORQUE)

            # 3) Apply torque to the motor (FFB) while holding position target
            # NaN target position means “use current target / current position” in position mode. 
            await c.set_position(
                position=math.nan,
                velocity=math.nan,
                feedforward_torque=torque_nm,
                kp_scale=KP_SCALE,
                kd_scale=KD_SCALE,
                maximum_torque=MAX_TORQUE,
                watchdog_timeout=0.1,
                query=False,
            ) 

            # 4) Send controls to the game (steering + pedals)
            steer = clamp(motor_pos_rot / STEER_RANGE_ROT, -1.0, 1.0)
            gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0)

            gas = clamp(float(phys.gas), 0.0, 1.0)      
            brake = clamp(float(phys.brake), 0.0, 1.0)  
            gamepad.right_trigger_float(value_float=gas)  
            gamepad.left_trigger_float(value_float=brake)


            gamepad.update()  

            await asyncio.sleep(0.004)  # ~250 Hz
    finally:
        mm.close() 

if __name__ == "__main__":
    asyncio.run(main())
