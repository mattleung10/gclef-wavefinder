import numpy as np
from zaber_motion import Units

from devices.MightexBufCmos import Camera
from devices.ZaberAdapter import ZaberAxis
from functions.image import frame_to_img, get_centroid_and_variance


class Focuser:
    def __init__(self,
                 camera : Camera | None,
                 f_axis : ZaberAxis | None,
                 steps  : int = 10,
                 min_move : float = 0.001) -> None:
        """Focuser class
        
        camera: MightexBufCmos Camera device
        f_axis: focal axis AxisModel
        steps: number of focus steps per pass
        min_move: minimum movement in mm
        """
        self.camera = camera
        self.f_axis = f_axis
        self.steps = steps
        self.min_move = min_move

    def focus(self) -> float:
        """Start the automatic focus routine

        returns the best focus position
        """
        focus_pos = 0.0
        if self.camera and self.f_axis:
            # set camera to trigger mode
            self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

            # set up for first pass
            limit_min = self.f_axis.axis.settings.get("limit.min",
                                                      Units.LENGTH_MILLIMETRES)
            limit_max = self.f_axis.axis.settings.get("limit.max",
                                                      Units.LENGTH_MILLIMETRES)
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (self.steps - 1)

            while step_dist >= self.min_move:
                focus_curve : dict[float,float] = {}

                for i in range(self.steps):
                    pos = travel_min + i * step_dist
                    self.f_axis.status = ZaberAxis.MOVING
                    self.f_axis.axis.move_absolute(pos, Units.LENGTH_MILLIMETRES,
                                                   wait_until_idle=True)
                    self.camera.trigger()
                    self.camera.acquire_frames()
                    frame = self.camera.get_newest_frame()
                    stats = get_centroid_and_variance(frame_to_img(frame.img))
                    # sqrt(var_x) * sqrt(var_y)
                    v = np.sqrt(stats[2]) * np.sqrt(stats[3])
                    focus_curve[pos] = v

                # find minimum along focus_curve
                focus_pos = min(focus_curve, key=focus_curve.get) # type: ignore

                # set up for next pass
                travel_min = np.clip(focus_pos - step_dist, limit_min, limit_max)
                travel_max = np.clip(focus_pos + step_dist, limit_min, limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (self.steps - 1)

            # move to focus position
            self.f_axis.status = ZaberAxis.MOVING      
            self.f_axis.axis.move_absolute(focus_pos, Units.LENGTH_MILLIMETRES,
                                           wait_until_idle=True)

        # return minimum position
        return focus_pos

        