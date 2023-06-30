from zaber_motion import Units
from zaber_motion.ascii import Axis
from devices.MightexBufCmos import Camera

class Focuser:
    def __init__(self, camera : Camera, axis : Axis) -> None:
        self.camera = camera
        self.axis = axis

    @staticmethod
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
                v = Focuser.compute_fwhm(frame.img)
            else:
                continue
            pos = axis.get_position()
            print(pos)
        
        return 0.0
        