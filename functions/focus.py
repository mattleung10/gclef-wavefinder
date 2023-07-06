import numpy as np
from zaber_motion import Units
from zaber_motion.ascii import Axis
from devices.MightexBufCmos import Camera, Frame

class Focuser:
    def __init__(self, camera : Camera | None, axis : Axis | None) -> None:
        self.camera = camera
        self.axis = axis

    @staticmethod
    def compute_fwhm(img) -> float:
        """Compute full width half max"""
        return 100.0
    
    def focus(self, steps_per_pass : int = 10, min_move : float = 0.001) -> float|None:
        """Start the automatic focus routine

        steps_per_pass: number of focus steps per pass
        min_move: minimum movement in mm
        
        returns the best focus position or None if failed
        """
        focus_pos = 0
        if self.camera and self.axis:
            # set camera to trigger mode
            self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

            # set up for first pass
            limit_min = self.axis.settings.get("limit.min", Units.LENGTH_MILLIMETRES)
            limit_max = self.axis.settings.get("limit.max", Units.LENGTH_MILLIMETRES)
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (steps_per_pass - 1)

            while step_dist >= min_move:
                focus_curve : dict[float,float] = {}

                for i in range(steps_per_pass):
                    pos = travel_min + i * step_dist
                    # TODO error handling on move
                    self.axis.move_absolute(pos, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
                    self.camera.trigger()
                    self.camera.acquire_frames()
                    # TODO check if frame is good
                    frame : Frame = self.camera.get_newest_frame() # type: ignore
                    fwhm = self.compute_fwhm(frame.img)
                    focus_curve[pos] = fwhm

                # TODO calculate minimum along focus_curve
                focus_pos = 5
                # set up for next pass
                travel_min = np.clip(focus_pos - step_dist, limit_min, limit_max)
                travel_max = np.clip(focus_pos + step_dist, limit_min, limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (steps_per_pass - 1)
            
            if focus_pos:
                self.axis.move_absolute(focus_pos, Units.LENGTH_MILLIMETRES, wait_until_idle=True)

        # return minimum position
        return focus_pos

        