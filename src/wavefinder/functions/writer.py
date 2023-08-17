import numpy as np
from astropy.io import fits
from astropy.time import Time
from PIL import Image

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera, Frame
from ..functions.focus import Focuser
from ..functions.position import Positioner
from ..functions.image import get_centroid_and_variance, variance_to_fwhm


class DataWriter:
    def __init__(self, camera: Camera | None, axes: dict[str, Axis], positioner: Positioner, focuser: Focuser) -> None:
        self.camera = camera
        self.axes = axes
        self.focuser = focuser

    def write_fits_file(self,
                        filename: str,
                        frame: Frame | None = None,
                        image: Image.Image | None = None):
        """Write a FITS file using most recent image and telemetry
        
        Args:
            filename: name of fits file to be written
            frame: write the given frame if not None, takes precedence over img
            image: write the given image if not None
        """

        hdu = fits.PrimaryHDU()
        hdu.header.update(self.make_general_headers())
        # use frame if provided, otherwise try img, otherwise make an img
        if frame:
            hdu.header.update(self.make_camera_frame_headers(frame))
            hdu.data = frame.img_array
        else:
            if image is None:
                image = Image.effect_noise(size=(1280, 960), sigma=100)
            hdu.header.update(self.make_dummy_frame_headers(image))
            hdu.data = np.array(image)
        for c in self.make_axis_headers():
            hdu.header['comment'] = c
        hdu.header.update(self.make_science_headers())
        hdu.add_checksum()
        hdu.writeto(filename, overwrite=True, output_verify='fix')

    def make_camera_frame_headers(self, frame: Frame) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to the camera image acquisition"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        if self.camera:
            headers['detector'] = (self.camera.modelno, "detector name")
        else:
            headers['detector'] = ("not_found",         "detector name")
        headers['date-obs'] = (frame.time.fits,     "observation date")
        headers['xposure']  = (frame.expTime,       "[ms] exposure time")
        headers['gain']     = (frame.gGain,         "[dB] detector gain")
        img = Image.fromarray(frame.img_array)
        headers.update(self.make_img_headers(img))
        return headers

    def make_dummy_frame_headers(self, img: Image.Image)-> dict[str, tuple[float | int | str, str]]:
        """Make fake camera headers"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers['detector'] = ("simulated", "detector name")
        headers.update(self.make_img_headers(img))
        return headers
    
    def make_img_headers(self, img: Image.Image) -> dict[str, tuple[float | int | str, str]]:
        """Make headers from image"""
        headers: dict[str, tuple[float | int | str, str]]= {}
        stats = get_centroid_and_variance(img)
        headers['cenx'] = (stats[0], "[px] centroid along x axis")
        headers['ceny'] = (stats[1], "[px] centroid along y axis")
        headers['fwhmx'] = (variance_to_fwhm(stats[2]), "[px] full width half maximum along x axis")
        headers['fwhmy'] = (variance_to_fwhm(stats[3]), "[px] full width half maximum along y axis")
        return headers

    def make_axis_headers(self) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to the motion axes"""
        headers: dict[str, tuple[float | int | str, str]]= {}
        for axis in self.axes.values():
            headers[axis.keyword] = (axis.position, f"[{axis.units[0]}] {axis.name} position")
        return headers
    
    def make_science_headers(self) -> dict[str, tuple[float | int | str, str]]:
        """Make headers related to this specific experiment"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers['wavelen']  = (0, "[nm] wavelength being measured")
        headers['order']    = (0, "diffraction order")
        if self.focuser.f_axis:
            headers['fcspnt']   = (self.focuser.best_focus, "[mm] focus position")
            dfcspnt = self.focuser.f_axis.position - self.focuser.best_focus
            headers['dfcspnt']  = (dfcspnt,                 "[mm] focal axis position minus focus position")
        return headers

    def make_general_headers(self) -> dict[str, tuple[str, str]]:
        """Make general, standard headers"""
        headers: dict[str, tuple[str, str]] = {}
        headers['date']     = (Time.now().fits,     "time this file was created, in UTC")
        headers['origin']   = ("CfA",               "institution which created this file")
        headers['creator']  = ("gclef-wavefinder",  "software which created this file")
        headers['instrume'] = ("G-CLEF_AIT",        "instrument name")
        headers['timesys']  = ("UTC",               "time coordinate system")
        headers['timeunit'] = ("s",                 "time unit")
        return headers