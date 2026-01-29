import asyncio
import math

import moteus
import vgamepad as vg
import ac_shared_memory as ac
import pedal

def clamp(x, lo, hi):
    """
    Prevents x values from goes below and above certain values
    
    :param x: x value
    :param lo: lower bound
    :param hi: higher bound
    """
    return lo if x < lo else hi if x > hi else x

async def main():
    gamepad = vg.VX360Gamepad()  # virtual Xbox360 pad 
    c = moteus.Controller()      # set id=... if needed 

    mm, phys = ac.open_ac_physics()  # AC shared memory 

    # Tune KP and KD in moteus config itself, -> moteus_gui.tview
    MAX_TORQUE = 1.5            # start low for safety 
    KP_SCALE = 1              # stiffness scaling in position mode 
    KD_SCALE = 1              # damping scaling in position mode 
    STEER_RANGE_ROT = 1.25      # rotations lock-to-lock/2 (example); tune to your wheel
    ROTATION_SCALE = 2.23       # rotation scale factor; tune to your wheel
    ZERO_OUT_ROTATION = 3.0  # rotation offset tune to your wheel


    try:
        st0 = await c.query()
        zero_pos = float(st0.values[moteus.Register.POSITION])
        #gamepad.right_trigger(255) # test going forward
        while True:
            # 1) Read moteus state
            st = await c.query()
            raw_pos = float(st.values[moteus.Register.POSITION])
            raw_vel = float(st.values[moteus.Register.VELOCITY])

            motor_pos_rot = (raw_pos - zero_pos - ZERO_OUT_ROTATION) * ROTATION_SCALE
            motor_vel_hz  = raw_vel
            print("pos " + str(motor_pos_rot))

            motor_pos_rad   = motor_pos_rot * 2.0 * math.pi
            motor_vel_rad_s = motor_vel_hz  * 2.0 * math.pi

            # 2) Compute FFB components (each function does ONE job)
            base_align_nm = ac.ffb_proxy_torque(phys, motor_pos_rad, motor_vel_rad_s)  # "normal driving" feel [file:1]
            kerb_slip_nm  = ac.ffb_offroad_rumble(phys)                                # kerb/slip bursts [file:1]

            road_nm = 0.0
            if hasattr(ac, "ffb_road_rumble"):
                road_nm = ac.ffb_road_rumble(phys)

            spin_nm = 0.0
            slide = 0.0
            if hasattr(ac, "ffb_spinout_effect"):
                spin_nm, slide = ac.ffb_spinout_effect(phys, motor_vel_rad_s)

            # 3) Mix (one place to reason about “what you feel”)
            # Go light during slide (reduce aligning torque)
            ALIGN_LIGHTEN = 0.7  # 0=no change, 1=remove base align completely
            base_align_nm *= (1.0 - ALIGN_LIGHTEN * slide)

            torque_nm = base_align_nm + kerb_slip_nm + road_nm + spin_nm
            torque_nm = clamp(torque_nm, -MAX_TORQUE, MAX_TORQUE)

            # 4) Command motor
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

            # 5) Find Pedal Angle
            gas_pedal_angle, brake_pedal_angle = pedal.read_pedal_degrees() # using default parameters
    
            if gas_pedal_angle is not None:
                # convert degree to trigger float
                gas_diff = 42.4 - 33.4 # adjust per setup
                gas_trigger_float = (gas_pedal_angle - 33.4) / gas_diff
                gas_trigger_float = clamp(gas_trigger_float, 0.0, 1.0)
                gamepad.right_trigger_float(gas_trigger_float)
            if brake_pedal_angle is not None:
                brake_diff = 186.33 - 168.33 # adjust
                brake_trigger_float = (brake_pedal_angle - 168.33) / brake_diff
                brake_trigger_float = clamp(brake_trigger_float, 0.0, 1.0)
                gamepad.left_trigger_float(brake_trigger_float)

            # 6) Send steering to game
            steer = clamp(motor_pos_rot / STEER_RANGE_ROT, -1.0, 1.0)
            gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0)
            gamepad.update()

            await asyncio.sleep(0.004)
    finally:
        mm.close() 

if __name__ == "__main__":
    asyncio.run(main())
