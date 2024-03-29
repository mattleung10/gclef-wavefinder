import copy
import random

import numpy as np
from astropy.io import fits
from astropy.time import Time
from PIL import Image

from ..devices.DkMonochromator import DkMonochromator

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera, Frame
from ..functions.image import find_centroid, find_full_width_half_max, threshold_copy
from ..gui.config import Configuration


class DataWriter:
    def __init__(
        self,
        camera: Camera | None,
        axes: dict[str, Axis],
        monochromator: DkMonochromator,
    ) -> None:
        self.camera = camera
        self.axes = axes
        self.monochromator = monochromator

    def write_fits_file(self, filename: str, config: Configuration):
        """Write a FITS file using most recent image and telemetry

        Args:
            filename: name of fits file to be written
            config: configuration at time of save
        """

        # make a copy of config so it doesn't change while writing
        self.config = copy.deepcopy(config)

        hdu = fits.PrimaryHDU()
        hdu.header.update(self.make_general_headers())
        hdu.header.update(self.make_science_headers())

        # use frame if possible, otherwise use full_image
        if self.config.camera_frame:
            hdu.header.update(self.make_camera_frame_headers(self.config.camera_frame))
            hdu.data = self.config.camera_frame.img_array
        else:
            hdu.header.update(self.make_dummy_frame_headers(self.config.full_img))
            hdu.data = np.array(self.config.full_img)
        hdu.header.update(self.make_axis_headers())
        hdu.add_checksum()
        hdu.writeto(filename, overwrite=True, output_verify="fix")

    def make_camera_frame_headers(
        self, frame: Frame
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to the camera image acquisition"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        if self.camera:
            headers["detector"] = (f"Mightex {self.camera.modelno}", "detector name")
        else:
            headers["detector"] = ("not_found", "detector name")
        headers["date-obs"] = (frame.time.fits, "observation date and time")  # type: ignore
        headers["xposure"] = (frame.expTime / 1000, "[s] exposure time")
        headers["gain"] = (frame.gGain, "[dB] detector gain")
        pxsizex, pxsizey = self.config.camera_pixel_size
        headers["pxsizex"] = (pxsizex, "[um] pixel size in x dimension")
        headers["pxsizey"] = (pxsizey, "[um] pixel size in y dimension")
        headers.update(self.make_image_headers(frame.img_array, frame.bits))
        return headers

    def make_dummy_frame_headers(
        self, img: Image.Image
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make fake camera headers"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers["detector"] = ("simulated", "detector name")
        headers.update(self.make_image_headers(np.array(img), 8))
        return headers

    def make_image_headers(
        self, img_array: np.ndarray, bits: int
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make headers from image"""

        threshold = (
            self.config.image_roi_threshold
            if self.config.image_use_roi_stats
            else self.config.image_full_threshold
        )

        headers: dict[str, tuple[float | int | str, str]] = {}
        headers["datamin"] = (float(0), "[counts] minimum possible pixel value")
        headers["datamax"] = (
            float((1 << bits) - 1),
            "[counts] maximum possible pixel value",
        )
        headers["threshld"] = (
            threshold,
            "[%] ignore pixels below this % of datamax",
        )
        # find centroid and FWHM
        image_copy = threshold_copy(img_array, bits, threshold)
        centroid = find_centroid(image_copy)
        fwhm = find_full_width_half_max(
            image_copy, centroid, self.config.image_fwhm_method
        )
        # skip if NaN
        if not np.isnan(centroid).any():
            headers["cenx"] = (centroid[0], "[px] centroid along x axis")
            headers["ceny"] = (centroid[1], "[px] centroid along y axis")
        if not np.isnan(fwhm):
            headers["fwhm"] = (fwhm, "[px] full width half maximum")
        return headers

    def make_axis_headers(self) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to the motion axes"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        for axis in self.axes.values():
            headers[axis.keyword] = (
                axis.position,
                f"[{axis.units[0]}] {axis.name} position",
            )
        return headers

    def make_science_headers(self) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to this specific experiment"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers["obstype"] = (self.config.image_obstype, "Type of observation taken")
        headers["object"] = (self.config.image_target, "target of the observation")
        headers["wavelen"] = (
            self.monochromator.current_wavelength,
            "[nm] wavelength being measured",
        )
        headers["order"] = (self.config.sequence_order, "diffraction order")
        headers["slit1"] = (
            self.monochromator.current_slit1,
            "[um] monochromator slit 1 (entry) size",
        )
        headers["slit2"] = (
            self.monochromator.current_slit2,
            "[um] monochromator slit 2 (exit) size",
        )
        id = f"{self.config.sequence_number:03}"
        id += f"-{self.config.sequence_order:03}"
        id += f"-{round(self.monochromator.current_wavelength):05}"
        id += f"-{random.randrange(16**4):04x}"  # random hash for uniqueness
        headers["obs_id"] = (id, "unique observation ID")
        if not np.isnan(self.config.focus_position):
            headers["focusz"] = (
                self.config.focus_position,
                "[mm] z-axis (focal axis) in-focus position",
            )
            headers["dfocusz"] = (
                self.axes[self.config.sequencer_z_axis].position
                - self.config.focus_position,
                "[mm] z-axis position minus in-focus position",
            )
        return headers

    def make_general_headers(self) -> dict[str, tuple[str, str]]:
        """Make general, standard headers"""
        headers: dict[str, tuple[str, str]] = {}
        headers["date"] = (Time.now().fits, "time this file was created, in UTC")  # type: ignore
        headers["origin"] = ("CfA", "institution which created this file")
        headers["creator"] = (
            f"gclef-wavefinder v{self.config.version}",
            "software which created this file",
        )
        headers["instrume"] = ("G-CLEF_AIT", "instrument name")
        headers["timesys"] = ("UTC", "time coordinate system")
        headers["timeunit"] = ("s", "time unit")
        return headers
