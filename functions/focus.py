import numpy as np
from zaber_motion import Units
from zaber_motion.exceptions import MotionLibException

from devices.MightexBufCmos import Camera, Frame
from devices.ZaberAdapter import AxisModel
from functions.image import frame_to_img, get_centroid_and_variance


class Focuser:
    def __init__(self, camera : Camera | None, f_axis : AxisModel | None) -> None:
        """Focuser class
        
        camera: MightexBufCmos Camera device
        f_axis: focal axis AxisModel
        """
        self.camera = camera
        self.f_axis = f_axis

    def focus(self, steps_per_pass : int = 10, min_move : float = 0.001) -> float|None:
        """Start the automatic focus routine

        steps_per_pass: number of focus steps per pass
        min_move: minimum movement in mm
        
        returns the best focus position or None if failed
        """
        focus_pos = None
        if self.camera and self.f_axis:
            # set camera to trigger mode
            self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

            # set up for first pass
            limit_min = self.f_axis.axis.settings.get("limit.min", Units.LENGTH_MILLIMETRES)
            limit_max = self.f_axis.axis.settings.get("limit.max", Units.LENGTH_MILLIMETRES)
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (steps_per_pass - 1)

            while step_dist >= min_move:
                focus_curve : dict[float,float] = {}

                for i in range(steps_per_pass):
                    pos = travel_min + i * step_dist
                    try:
                        self.f_axis.axis.move_absolute(pos, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
                        self.f_axis.status = AxisModel.MOVING
                    except MotionLibException:
                        self.f_axis.status = AxisModel.ERROR
                        return None
                    
                    self.camera.trigger()
                    self.camera.acquire_frames()
                    frame : Frame = self.camera.get_newest_frame() # type: ignore
                    if frame:
                        stats = get_centroid_and_variance(frame_to_img(frame.img))
                        v = np.sqrt(stats[2]) * np.sqrt(stats[3]) # sqrt(var_x) * sqrt(var_y)
                        focus_curve[pos] = v
                    else:
                        return None

                # find minimum along focus_curve
                focus_pos = min(focus_curve, key=focus_curve.get) # type: ignore

                # set up for next pass
                travel_min = np.clip(focus_pos - step_dist, limit_min, limit_max)
                travel_max = np.clip(focus_pos + step_dist, limit_min, limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (steps_per_pass - 1)
            
            if focus_pos:
                self.f_axis.axis.move_absolute(focus_pos, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
                self.f_axis.status = AxisModel.MOVING

        # return minimum position
        return focus_pos

        