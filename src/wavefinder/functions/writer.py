import numpy as np
from astropy.io import fits
from astropy.time import Time
from PIL import Image

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera, Frame
from ..functions.focus import Focuser
from ..functions.image import get_centroid_and_variance, variance_to_fwhm
from ..functions.position import Positioner
from ..gui.config import Configuration


class DataWriter:
    def __init__(
        self,
        config: Configuration,
        camera: Camera | None,
        axes: dict[str, Axis],
        positioner: Positioner,
        focuser: Focuser,
    ) -> None:
        self.config = config
        self.camera = camera
        self.axes = axes
        self.positioner = positioner
        self.focuser = focuser

    def write_fits_file(
        self,
        filename: str,
        frame: Frame | None = None,
        image: Image.Image | None = None,
        obstype: str = "",
        target: str = "",
        wavelength: float = 0.0,
        order: int = 0
    ):
        """Write a FITS file using most recent image and telemetry

        Args:
            filename: name of fits file to be written
            frame: write the given frame if not None, takes precedence over image
            image: write the given image if not None
            obstype: observation type; see config.py for list
            target: name of target object
            wavelength: input light source wavelength in nm
            order: defraction order
        """

        # set default obstype
        if obstype == "":
            obstype = self.config.writer_obstypes[0]

        hdu = fits.PrimaryHDU()
        hdu.header.update(self.make_general_headers())
        hdu.header.update(self.make_science_headers(obstype, target, wavelength, order))

        # use frame if provided, otherwise try img, otherwise make an img
        if frame:
            hdu.header.update(self.make_camera_frame_headers(frame))
            hdu.data = frame.img_array
        else:
            if image is None:
                image = Image.effect_noise(size=(1280, 960), sigma=100)
            hdu.header.update(self.make_dummy_frame_headers(image))
            hdu.data = np.array(image)
        hdu.header.update(self.make_axis_headers())
        hdu.add_checksum()
        hdu.writeto(filename, overwrite=True, output_verify="fix")

    def make_camera_frame_headers(
        self, frame: Frame
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to the camera image acquisition"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        if self.camera:
            headers["detector"] = ("Mightex " + self.camera.modelno, "detector name")
        else:
            headers["detector"] = ("not_found", "detector name")
        headers["date-obs"] = (frame.time.fits, "observation date and time")  # type: ignore
        headers["xposure"] = (frame.expTime / 1000, "[s] exposure time")
        headers["gain"] = (frame.gGain, "[dB] detector gain")
        pxsizex, pxsizey = self.positioner.px_size
        headers["pxsizex"] = (pxsizex, "[um] pixel size in x dimension")
        headers["pxsizey"] = (pxsizey, "[um] pixel size in y dimension")
        headers.update(self.make_img_headers(frame.img_array, frame.bits))
        return headers

    def make_dummy_frame_headers(
        self, img: Image.Image
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make fake camera headers"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers["detector"] = ("simulated", "detector name")
        headers.update(self.make_img_headers(np.array(img), 8))
        return headers

    def make_img_headers(
        self, img_array: np.ndarray, bits: int
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make headers from image"""
        threshold = (
            self.config.image_roi_threshold
            if self.config.image_use_roi_stats
            else self.config.image_full_threshold
        )

        headers: dict[str, tuple[float | int | str, str]] = {}
        stats = get_centroid_and_variance(img_array, bits, threshold)
        headers["datamin"] = (float(0), "[counts] minimum possible pixel value")
        headers["datamax"] = (
            float((1 << bits) - 1),
            "[counts] maximum possible pixel value",
        )
        headers["threshld"] = (
            threshold,
            "[%] ignore pixels below this % of datamax",
        )
        headers["cenx"] = (stats[0], "[px] centroid along x axis")
        headers["ceny"] = (stats[1], "[px] centroid along y axis")
        headers["fwhmx"] = (
            variance_to_fwhm(stats[2]),
            "[px] full width half maximum along x axis",
        )
        headers["fwhmy"] = (
            variance_to_fwhm(stats[3]),
            "[px] full width half maximum along y axis",
        )
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

    def make_science_headers(
        self,
        obstype: str = "",
        target: str = "",
        wavelength: float = 0.0,
        order: int = 0,
    ) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to this specific experiment
        
        Args:
            obstype: observation type; see config.py for list
            target: name of target object
            wavelength: input light source wavelength in nm
            order: defraction order
        """
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers["obstype"] = (obstype, "Type of observation taken")
        headers["object"] = (target, "target of the observation")
        headers["wavelen"] = (wavelength, "[nm] wavelength being measured")
        headers["order"] = (order, "diffraction order")
        if self.focuser.f_axis:
            headers["focusz"] = (
                self.focuser.best_focus,
                "[mm] z-axis (focal axis) in-focus position",
            )
            dfocusz = self.focuser.f_axis.position - self.focuser.best_focus
            headers["dfocusz"] = (
                dfocusz,
                "[mm] z-axis position minus in-focus position",
            )
        return headers

    def make_general_headers(self) -> dict[str, tuple[str, str]]:
        """Make general, standard headers"""
        headers: dict[str, tuple[str, str]] = {}
        headers["date"] = (Time.now().fits, "time this file was created, in UTC")  # type: ignore
        headers["origin"] = ("CfA", "institution which created this file")
        headers["creator"] = ("gclef-wavefinder", "software which created this file")
        headers["instrume"] = ("G-CLEF_AIT", "instrument name")
        headers["timesys"] = ("UTC", "time coordinate system")
        headers["timeunit"] = ("s", "time unit")
        return headers
