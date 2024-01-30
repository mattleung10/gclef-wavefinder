import asyncio
import tkinter as tk

import numpy as np

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera
from ..gui.config import Configuration
from .image import get_roi_box, image_math, roi_copy


class Sequencer:
    def __init__(
        self, config: Configuration, camera: Camera | None, axes: dict[str, Axis]
    ) -> None:
        """Multi-function sequencer class has methods to:

        1. Auto-center image
        1. Auto-focus image
        1. Read in a sequence table, and for each row:
                - move to position
                - center image
                - focus image
                - take 3 images: [negative offset, on focus, positive offset]
                - save images and any other data

        Args:
            config: application configuration
            camera: MightexBufCmos Camera device
            axes: dict of all motion axes
        """
        self.config = config
        self.camera = camera
        self.axes = axes
        self.sequence: list[dict[str, float]] = list()

        # check for axes
        if not self.config.sequencer_x_axis in self.axes:
            print("Sequencer x-axis not found.")
        if not self.config.sequencer_y_axis in self.axes:
            print("Sequencer y-axis not found.")
        if not self.config.sequencer_z_axis in self.axes:
            print("Sequencer z-axis not found.")

    async def center(
        self,
        image_size: tuple[int, int],
        centroid: tuple[float, float] | None = None,
    ) -> tuple[float, float]:
        """Move the x and y axes to center the centroid

        X is mirrored. Dones nothing on error.

        Args:
            image_size: (x_size, y_size) full image size
            centroid: tuple of (float, float) giving the computed centroid of the image;
                        if not provided, use config.image_centroid

        Returns center position in mm
        """
        if not centroid:
            centroid = self.config.image_centroid
        px_size = self.config.camera_pixel_size
        x_axis = self.axes.get(self.config.sequencer_x_axis)
        y_axis = self.axes.get(self.config.sequencer_y_axis)
        centered_position = (np.nan, np.nan)

        if (
            np.greater(image_size, 0).all()
            and not np.isnan(centroid).any()
            and np.greater(px_size, 0).all()
            and x_axis
            and y_axis
        ):
            img_center = (image_size[0] / 2, image_size[1] / 2)
            move_x_px = -(centroid[0] - img_center[0])  # X is mirrored
            move_y_px = centroid[1] - img_center[1]
            await x_axis.move_relative((move_x_px * px_size[0]) / 1000)
            await y_axis.move_relative((move_y_px * px_size[1]) / 1000)
            centered_position = (x_axis.position, y_axis.position)
        return centered_position

    async def focus(self) -> float:
        """Start the automatic focus routine

        returns the best focus position
        """
        z_axis = self.axes.get(self.config.sequencer_z_axis)
        fpp = self.config.focus_frames_per_point
        ppp = self.config.focus_points_per_pass
        min_move = self.config.focus_minimum_move

        focus_pos = z_axis.position if z_axis else np.nan

        if self.camera and z_axis:
            # set camera to trigger mode
            old_mode = self.camera.run_mode
            await self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)
            self.config.image_math_in_function = True

            # set up for first pass
            limit_min, limit_max = await z_axis.get_limits()
            travel_min = limit_min
            travel_max = limit_max
            travel_dist = travel_max - travel_min
            step_dist = travel_dist / (ppp - 1)
            pass_i = 0

            while step_dist >= min_move:
                # keep focusing until each move is min_move distance
                focus_curve: dict[float, float] = {}

                for point_i in range(ppp):
                    # for each point in this pass
                    pos = travel_min + point_i * step_dist
                    await z_axis.move_absolute(pos)
                    sum = 0

                    for _ in range(fpp):
                        # for each frame at this point
                        await self.camera.clear_buffer()
                        await self.camera.trigger()
                        # wait for frame
                        while True:
                            try:
                                frame = self.camera.get_newest_frame()
                                break
                            except IndexError:
                                # sleep is necessary to give other tasks time to process
                                await asyncio.sleep(0.1)
                                continue
                        # use ROI if selected
                        if self.config.image_use_roi_stats:
                            image_array = roi_copy(
                                frame.img_array, self.config.roi_size
                            )
                            threshold = self.config.image_roi_threshold
                        else:
                            image_array = frame.img_array
                            threshold = self.config.image_full_threshold

                        # compute image stats
                        centroid, fwhm, max_value, n_saturated = image_math(
                            image_array,
                            frame.bits,
                            threshold,
                            self.config.image_fwhm_method,
                        )
                        # translate to full-frame pixel coordinates
                        if self.config.image_use_roi_stats:
                            box = get_roi_box(
                                (frame.rows, frame.cols), self.config.roi_size
                            )
                            centroid = (centroid[0] + box[0], centroid[1] + box[1])
                        # store values for GUI to see
                        self.config.image_centroid = centroid
                        self.config.image_fwhm = fwhm
                        self.config.image_max_value = max_value
                        self.config.image_n_saturated = n_saturated

                        # use fwhm of thresholded image as metric for focus quality
                        # if fwhm is NaN, sum will be NaN and thrown out
                        sum += fwhm

                    # insert average fwhm into focus curve if it exists
                    if not np.isnan(sum):
                        focus_curve[pos] = sum / fpp

                # find minimum along focus_curve
                focus_pos = min(focus_curve, key=focus_curve.get, default=focus_pos)  # type: ignore

                # set up for next pass
                travel_min = min(max(focus_pos - step_dist, limit_min), limit_max)
                travel_max = min(max(focus_pos + step_dist, limit_min), limit_max)
                travel_dist = travel_max - travel_min
                step_dist = travel_dist / (ppp - 1)
                pass_i += 1

            # move to focus position
            await z_axis.move_absolute(focus_pos)
            # restore previous camera mode
            await self.camera.set_mode(run_mode=old_mode, write_now=True)
            self.config.image_math_in_function = False

        # return best position
        self.config.focus_position = focus_pos
        return focus_pos

    def read_input_file(self, filename: str):
        """Read input sequence file

        Args:
            filename: path to filename
        """
        with open(filename) as f:
            # reset the sequence
            self.sequence = list()
            # set headers, strip whitespace from header names
            header_line = f.readline()
            headers = [h.strip() for h in header_line.split(",")]

            # this loop will start with the 2nd line because the previous
            # readline has advanced the buffer's iterator0
            for line in f:
                # make a dict, using the header values
                d: dict[str, float] = {}
                for i, n in enumerate(line.split(",")):
                    d[headers[i]] = float(n)
                self.sequence.append(d)

    async def run_sequence(self, output_dir: str, status_text: tk.StringVar):
        """Run sequence and store data in output directory

        Args:
            output_dir: path to output directory
            status_text: Tk StringVar to update with status
        """

        # TODO set camera to trigger mode
        # old_mode = self.camera.run_mode
        # await self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

        for i, row in enumerate(self.sequence):
            print(self.axes)
            # 1) move to position
            for col in row:
                # match header with motion axis, then move to position
                a = self.axes.get(col)
                if a:
                    await a.move_absolute(row[col])
            # 2) center image
            # TODO: clear buffer, take image
