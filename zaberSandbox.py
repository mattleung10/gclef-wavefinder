from zaber_motion import Units
from zaber_motion.ascii import Connection

SN_X = 33938
SN_Y = 33937
SN_Z = 33939

with Connection.open_serial_port("/dev/ttyUSB0") as connection:
    connection.enable_alerts()

    device_list = connection.detect_devices()
    det_stage_x = next(filter(lambda d: d.serial_number == SN_X, device_list))
    det_stage_y = next(filter(lambda d: d.serial_number == SN_Y, device_list))
    det_stage_z = next(filter(lambda d: d.serial_number == SN_Z, device_list))
    det_stages = [det_stage_x, det_stage_y, det_stage_z]

    det_ax = det_stage_x.get_axis(1)
    det_ay = det_stage_y.get_axis(1)
    det_az = det_stage_z.get_axis(1)
    det_axes = [det_ax, det_ay, det_az]

    for axis in det_axes:
      if not axis.is_homed():
        axis.home()
    
    det_ax.move_max()

    print(det_ax.get_position(unit=Units.LENGTH_MILLIMETRES))

    # axis = device.get_axis(1)
    # if not axis.is_homed():
    #   axis.home()

    # # Move to 10mm
    # axis.move_absolute(10, Units.LENGTH_MILLIMETRES)

    # # Move by an additional 5mm
    # axis.move_relative(5, Units.LENGTH_MILLIMETRES)