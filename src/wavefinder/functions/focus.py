import asyncio

import numpy as np

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera
from ..gui.config import Configuration
from .image import get_centroid_and_variance


class Focuser:
    def __init__(
        self,
        config: Configuration,
        camera: Camera | None,
        f_axis: Axis | None,
        focus_points_per_pass: int = 10,
        focus_frames_per_point: int = 3,
        minimum_move: float = 0.001,
    ) -> None:
        """Focuser class

        Args:
            config: application configuration
            camera: MightexBufCmos Camera device
            f_axis: focal axis handle
            focus_points_per_pass: number of focus steps per pass
            focus_frames_per_point: number of frames to average per focus point
            minimum_move: minimum movement in mm
        """
        self.config = config
        self.camera = camera
        self.f_axis = f_axis
        self.points_per_pass = focus_points_per_pass
        self.frames_per_point = focus_frames_per_point
        self.min_move = minimum_move

        self.best_focus = 0.0

        if not self.f_axis:
            print("Camera focuser z-axis not found.")

    async def focus(self) -> float:
        """Start the automatic focus routine

        returns the best focus position
        """
        threshold = (
            self.config.image_roi_threshold
            if self.config.image_use_roi_stats
            else self.config.image_full_threshold
        )

        focus_pos = self.f_axis.position if self.f_axis else 0.0
        if self.camera and self.f_axis:
            # set camera to trigger mode
            old_mode = self.camera.run_mode
            await self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

            # set up for first pass
            limit_min, limit_max = await self.f_axis.get_limits()
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (self.points_per_pass - 1)
            pass_i = 0

            while step_dist >= self.min_move:
                focus_curve: dict[float, float] = {}

                for point_i in range(self.points_per_pass):
                    pos = travel_min + point_i * step_dist
                    await self.f_axis.move_absolute(pos)
                    sum = 0

                    for frame_i in range(self.frames_per_point):
                        await self.camera.trigger()

                        # if this frame isn't the right trigger, wait
                        exp_nTriggers = (frame_i + 1) + self.frames_per_point * (
                            point_i + self.points_per_pass * pass_i
                        )
                        frame = self.camera.get_newest_frame()
                        nT = frame.nTriggers
                        while nT < exp_nTriggers:
                            # sleep is necessary to give other tasks time to process
                            await asyncio.sleep(0.1)
                            frame = self.camera.get_newest_frame()
                            nT = frame.nTriggers

                        # compute focus
                        # TODO use new fwhm methods
                        stats = get_centroid_and_variance(
                            frame.img_array, frame.bits, threshold
                        )
                        # sqrt(var_x) * sqrt(var_y)
                        v = np.sqrt(stats[2]) * np.sqrt(stats[3])
                        sum += v
                    
                    # ignore if no pixels above threshold
                    if sum != 0:
                        focus_curve[pos] = sum / self.frames_per_point

                # find minimum along focus_curve
                focus_pos = min(focus_curve, key=focus_curve.get, default=focus_pos)  # type: ignore

                # set up for next pass
                travel_min = min(max(focus_pos - step_dist, limit_min), limit_max)
                travel_max = min(max(focus_pos + step_dist, limit_min), limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (self.points_per_pass - 1)
                pass_i += 1

            # move to focus position
            await self.f_axis.move_absolute(focus_pos)

            # restore previous camera mode
            await self.camera.set_mode(run_mode=old_mode, write_now=True)

        # return best position
        self.best_focus = focus_pos
        return focus_pos
