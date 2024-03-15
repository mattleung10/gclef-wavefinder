import asyncio
import os
from enum import StrEnum

import numpy as np
from astropy.time import Time

from ..devices.Axis import Axis
from ..devices.DkMonochromator import DkMonochromator
from ..devices.MightexBufCmos import Camera, Frame
from ..gui.config import Configuration
from .image import get_roi_box, image_math, roi_copy
from .writer import DataWriter


class SequenceState(StrEnum):
    INPUT = "Select Input File"
    NOT_READY = "Can't Run Sequence"
    READY = "Ready to Run"
    RUN = "Running"
    FINISHED = "Finished"
    ABORT = "Aborted"


class SequenceSubstate(StrEnum):
    START = "Start Step"
    WAVELENGTH = "Set Monochromator Wavelength"
    MOVE = "Move to Position"
    CENTER = "Center Image"
    FOCUS = "Focus Image"
    CAPTURE_F = "Take In-Focus Image"
    CAPTURE_D = "Take Delta Focus Images"
    FINISHED = "Finished"


class Sequencer:
    def __init__(
        self,
        config: Configuration,
        camera: Camera | None,
        axes: dict[str, Axis],
        monochromator: DkMonochromator,
        data_writer: DataWriter,
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
            data_writer: DataWriter object
        """
        self.config = config
        self.camera = camera
        self.old_camera_mode = Camera.NORMAL
        self.axes = axes
        self.monochromator = monochromator
        self.data_writer = data_writer
        self.sequence: list[dict[str, list[float]]] = list()
        self.sequence_iteration = 0
        self.sequence_state: SequenceState = SequenceState.INPUT
        self.sequence_substate: SequenceSubstate = SequenceSubstate.START
        self.abort = False

        # check for axes
        if not self.config.sequencer_x_axis in self.axes:
            print("Sequencer x axis not found.")
        if not self.config.sequencer_y_axis in self.axes:
            print("Sequencer y axis not found.")
        if not self.config.sequencer_z_axis in self.axes:
            print("Sequencer z axis not found.")

    async def center(
        self,
        image_size: tuple[int, int],
        centroid: tuple[float, float] | None = None,
    ) -> tuple[float, float]:
        """Move the x and y axes to center the centroid

        Dones nothing on error.

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
            move_x_px = centroid[0] - img_center[0]
            # y is mirrored
            move_y_px = -(centroid[1] - img_center[1])
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
                    # check for error
                    if z_axis.status == Axis.ERROR:
                        print("Error in focus routine!")
                        return -1
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
                        # compute image stats and use fwhm of thresholded image as metric for focus quality
                        _, fwhm, _, _ = self.compute_image_stats(frame)
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

        # return best position
        self.config.focus_position = focus_pos
        return focus_pos

    def read_input_file(self, filename: str):
        """Read input sequence file

        Args:
            filename: path to filename
        """
        self.sequence_state = SequenceState.NOT_READY
        with open(filename) as f:
            # reset the sequence
            self.sequence = list()
            # set headers, strip whitespace from header names
            # set headers to lowercase
            header_line = f.readline()
            headers = [h.strip().lower() for h in header_line.split(",")]

            # this loop will start with the 2nd line because the previous
            # readline has advanced the buffer's iterator
            for line in f:
                # make a dict, using the header values
                d: dict[str, list[float]] = {}
                for i, col in enumerate(line.split(",")):
                    d[headers[i]] = [float(x) for x in col.split()]
                self.sequence.append(d)
            if self.is_sequence_runnable() is True:
                self.sequence_state = SequenceState.READY

    def is_sequence_runnable(self):
        """Check if the sequence can be run"""
        if len(self.sequence) == 0:
            return False
        elif self.camera is None:
            return False
        elif self.monochromator.comm_up is False:
            return False
        if not self.config.sequencer_x_axis in self.axes:
            return False
        if not self.config.sequencer_y_axis in self.axes:
            return False
        if not self.config.sequencer_z_axis in self.axes:
            return False
        else:
            return True

    async def run_sequence(self, output_dir: str):
        """Run sequence and store data in output directory

        Args:
            output_dir: path to output directory
        """

        # check for necessary devices and sequence
        # already checked by read_input_file, so shouldn't happen
        if not self.is_sequence_runnable() or self.camera is None:
            self.sequence_state = SequenceState.ABORT
            return

        self.sequence_state = SequenceState.RUN
        # set camera to trigger mode
        self.old_camera_mode = self.camera.run_mode
        await self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

        j = 1  # image sequence number
        for self.sequence_iteration, row in enumerate(self.sequence):
            ## 0) update parameters and status text
            if not await self.sequence_housekeeping(SequenceSubstate.START):
                return
            order = int(row["order"][0])
            wavel = row["wavelength"][0]
            self.config.sequence_number = j
            self.config.sequence_order = order

            ## 1) set monochromator wavelength
            if not await self.sequence_housekeeping(SequenceSubstate.WAVELENGTH):
                return
            self.monochromator.target_wavelength = wavel
            self.monochromator.q.put(self.monochromator.go_to_target_wavelength)
            await self.monochromator.wait_for_wavelength()

            ## 2) move to position
            for col in row:
                if not await self.sequence_housekeeping(SequenceSubstate.MOVE):
                    return
                # match header with motion axis, then move to position
                a = self.axes.get(col)
                if a:
                    await a.move_absolute(row[col][0])

            ## 3) take image for centroid, compute centroid, center image
            if not await self.sequence_housekeeping(SequenceSubstate.CENTER):
                return
            frame = await self.take_image(self.camera)
            centroid, _, _, _ = self.compute_image_stats(frame)
            image_size = (frame.img_array.shape[1], frame.img_array.shape[0])
            await self.center(image_size, centroid)

            ## 4) find best focus
            if not await self.sequence_housekeeping(SequenceSubstate.FOCUS):
                return
            await self.focus()

            ## 5) take at-focus image, save, and increment sequence
            if not await self.sequence_housekeeping(SequenceSubstate.CAPTURE_F):
                return
            self.config.camera_frame = await self.take_image(self.camera)
            t = Time.now()
            datestr = f"{t.ymdhms[0]:04}{t.ymdhms[1]:02}{t.ymdhms[2]:02}"
            # example name "gclef_20240131_ait_007_08500_0005_f.fits"
            # means date is 2024-01-31, order = 7, wavelen = 8500nm
            #       5th observation in sequence, "f" for in-focus
            letter = "f"
            basename = (
                f"gclef_ait_{datestr}_{order:03}_{round(wavel):05}_{j:03}_{letter}.fits"
            )
            filename = os.path.join(output_dir, basename)
            self.data_writer.write_fits_file(filename, self.config)
            j += 1

            ## 6) intra- and extra- focus positions
            z_axis = self.axes.get(self.config.sequencer_z_axis)
            if z_axis:
                # for each z position in the delta focus list
                for p in row["dfocusz"]:
                    if not await self.sequence_housekeeping(SequenceSubstate.CAPTURE_D):
                        return
                    ### 6.1) move to position
                    await z_axis.move_absolute(p + self.config.focus_position)
                    ### 6.2) take image
                    frame = await self.take_image(self.camera)
                    self.config.camera_frame = frame
                    ### 6.3) compute image statistics
                    centroid, _, _, _ = self.compute_image_stats(frame)
                    ### 6.4) save and increment sequence
                    # "i" for intra-focus (dfocusz > 0); "e" for extra-focus
                    letter = "f" if p == 0 else "i" if p < 0 else "e"
                    basename = f"gclef_ait_{datestr}_{order:03}_{round(wavel):05}_{j:03}_{letter}.fits"
                    filename = os.path.join(output_dir, basename)
                    self.data_writer.write_fits_file(filename, self.config)
                    j += 1

        if not await self.sequence_housekeeping(SequenceSubstate.FINISHED):
            return

        # restore previous camera mode
        await self.camera.set_mode(run_mode=self.old_camera_mode, write_now=True)
        self.sequence_state = SequenceState.FINISHED

    def abort_sequence(self):
        """Abort running sequence"""
        self.abort = True

    async def sequence_housekeeping(self, substate: SequenceSubstate):
        """Housekeeping to update the GUI

        Args:
            substate: sequence substate

        Returns True unless abort
        """
        self.sequence_substate = substate
        if self.abort:
            self.sequence_state = SequenceState.ABORT
            self.sequence.clear()
            if self.camera:
                await self.camera.set_mode(
                    run_mode=self.old_camera_mode, write_now=True
                )
            self.abort = False  # reset abort signal
            return False
        else:
            return True

    async def take_image(self, camera: Camera):
        """Take image for use in sequencer.

        Args:
            camera: Camera, not None

        Returns frame
        """
        await camera.clear_buffer()
        await camera.trigger()
        # wait for frame
        while True:
            try:
                frame = camera.get_newest_frame()
                break
            except IndexError:
                # sleep is necessary to give other tasks time to process
                await asyncio.sleep(0.1)
                continue
        return frame

    def compute_image_stats(self, frame: Frame):
        """Compute image statistics for use in sequencer.

        Args:
            frame: captured image frame

        Returns centroid, fwhm, max_value, n_saturated
        """
        # use ROI if selected
        if self.config.image_use_roi_stats:
            image_array = roi_copy(frame.img_array, self.config.roi_size)
            threshold = self.config.image_roi_threshold
        else:
            image_array = frame.img_array
            threshold = self.config.image_full_threshold

        centroid, fwhm, max_value, n_saturated = image_math(
            image_array,
            frame.bits,
            threshold,
            self.config.image_fwhm_method,
        )
        # translate to full-frame pixel coordinates
        if self.config.image_use_roi_stats:
            box = get_roi_box((frame.rows, frame.cols), self.config.roi_size)
            centroid = (centroid[0] + box[0], centroid[1] + box[1])
        # store values for GUI to see
        self.config.image_centroid = centroid
        self.config.image_fwhm = fwhm
        self.config.image_max_value = max_value
        self.config.image_n_saturated = n_saturated

        return centroid, fwhm, max_value, n_saturated
