from zaber_motion import Units
from zaber_motion.ascii import Connection, Axis
from devices.MightexBufCmos import Camera

def compute_fwhm(img) -> float:
    """Compute full width half max"""
    return 100.0

def focus(camera : Camera, axis : Axis) -> float:
    """Find best axis position such that camera is in focus
    
    camera: MightexBufCmos Camera object
    axis: Zaber z-axis handle

    returns focused position in micrometers
    """

    # start at minimum
    axis.move_min()
    u_step = 1000 # micrometers
    pos_max = axis.settings.get("limit.max")
    pos = 0
    
    while pos <= pos_max:
        axis.move_relative(u_step, Units.LENGTH_MICROMETRES)
        camera.trigger()
        camera.acquire_frames()
        frame = camera.get_newest_frame()
        if frame:
            v = compute_fwhm(frame.img)
        else:
            continue
        pos = axis.get_position()
        print(pos)
    
    return 0.0

if __name__ == "__main__":
    SN_Z = 33939

    with Connection.open_serial_port("/dev/ttyUSB0") as connection:
        connection.enable_alerts()

        det_stage_z = next(filter(lambda d: d.serial_number == SN_Z, connection.detect_devices()))
        det_az = det_stage_z.get_axis(1)
        camera = Camera(run_mode=Camera.TRIGGER)

        if not det_az.is_homed():
            det_az.home()

        print(focus(camera, det_az))

        