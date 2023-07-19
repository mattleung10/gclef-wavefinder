import numpy as np
from zaber_motion import Units

from devices.MightexBufCmos import Camera
from devices.Axis import Axis
from functions.image import frame_to_img, get_centroid_and_variance


class Focuser:
    def __init__(self,
                 camera : Camera | None,
                 f_axis : Axis | None,
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

    async def focus(self) -> float:
        """Start the automatic focus routine

        returns the best focus position
        """
        focus_pos = 0.0
        if self.camera and self.f_axis:
            # set camera to trigger mode
            self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

            # set up for first pass
            limit_min, limit_max = await self.f_axis.get_limits()
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (self.steps - 1)
            n_pass = 0

            while step_dist >= self.min_move:
                focus_curve : dict[float,float] = {}

                for i in range(self.steps):
                    pos = travel_min + i * step_dist
                    await self.f_axis.move_absolute(pos)
                    self.camera.trigger()
                    # NOTE camera_panel loop is also acquiring frames, may conflict
                    self.camera.acquire_frames()
                    frame = self.camera.get_newest_frame()

                    # if this frame isn't the right trigger, wait
                    exp_nTriggers = (i+1) + self.steps*n_pass
                    while frame.nTriggers < exp_nTriggers:
                        frame = self.camera.get_newest_frame()

                    stats = get_centroid_and_variance(frame_to_img(frame.img))
                    # sqrt(var_x) * sqrt(var_y)
                    v = np.sqrt(stats[2]) * np.sqrt(stats[3])
                    # print(round(pos,3), round(v, 3), frame.nTriggers, frame.timestamp)
                    focus_curve[pos] = v

                # find minimum along focus_curve
                focus_pos = min(focus_curve, key=focus_curve.get) # type: ignore

                # set up for next pass
                travel_min = np.clip(focus_pos - step_dist, limit_min, limit_max)
                travel_max = np.clip(focus_pos + step_dist, limit_min, limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (self.steps - 1)
                n_pass += 1

            # move to focus position 
            await self.f_axis.move_absolute(focus_pos)
            
            # set camera to stream mode
            self.camera.set_mode(run_mode=Camera.NORMAL, write_now=True)

        # return minimum position
        return focus_pos

        