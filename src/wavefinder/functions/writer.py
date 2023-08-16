import numpy as np
from astropy.io import fits
from astropy.time import Time
from PIL import Image

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera
from ..functions.focus import Focuser
from ..functions.position import Positioner


class DataWriter:
    def __init__(self, camera: Camera | None, axes: dict[str, Axis], positioner: Positioner, focuser: Focuser) -> None:
        self.camera = camera
        self.axes = axes
        self.focuser = focuser

    def write_fits_file(self,
                        filename: str,
                        img: np.ndarray | None = None):
        """Write a FITS file using most recent image and telemetry
        
        Args:
            filename: name of fits file to be written
            img: write the given image if not None
        """

        hdu = fits.PrimaryHDU()

        hdu.header.update(self.make_general_headers())
        if self.camera:
            # get the img if not provided
            if img is None:
                img = np.array(self.camera.get_newest_frame())
            hdu.header.update(self.make_camera_frame_headers())            
        else:
            # No camera, write dummy file
            if img is None:
                img = np.array(Image.effect_noise(size=(1280, 960), sigma=100))
            hdu.header.update(self.make_dummy_frame_headers())
        
        for c in self.make_axis_headers():
            hdu.header['comment'] = c
        hdu.header.update(self.make_axis_headers())
        hdu.header.update(self.make_science_headers())
        hdu.data = img
        hdu.add_checksum()
        hdu.writeto(filename, overwrite=True, output_verify='fix')

    def make_camera_frame_headers(self) -> dict[str, tuple[str, str]]:
        """Make headers related to the camera image acquisition"""
        headers: dict[str, tuple[str, str]] = {}
        if self.camera:
            frame = self.camera.get_newest_frame()
            headers['detector'] = (self.camera.modelno, "detector name")
            headers['date-obs'] = (frame.time.fits,     "observation date")
            headers['xposure']  = (frame.expTime,       "[ms] exposure time")
            headers['gain']     = (frame.gGain,         "[dB] detector gain")
        return headers

    def make_dummy_frame_headers(self) -> dict[str, tuple[str, str]]:
        """Make fake camera headers"""
        headers: dict[str, tuple[str, str]] = {}
        headers['detector'] = ("simulated", "detector name")
        return headers

    def make_axis_headers(self) -> list[str]:
        """Make headers related to the motion axes"""
        comments: list[str] = list()
        for axis in self.axes.values():
            comments.append((f"{axis.name} position: {axis.position}"))
        return comments
    
    def make_science_headers(self):
        """Make headers related to this specific experiment"""
        headers: dict[str, tuple[float | int | str, str]] = {}
        headers['fcspnt']   = (self.focuser.best_focus, "focus position")
        headers['dfcspnt']  = (0,                       "distance to focus position")
        return headers

    def make_general_headers(self) -> dict[str, tuple[str, str]]:
        """Make general, standard headers"""
        headers: dict[str, tuple[str, str]] = {}
        headers['date']     = (Time.now().fits,     "time in UTC")
        headers['origin']   = ("CfA",               "instituion which created this file")
        headers['creator']  = ("gclef-wavefinder",  "software which created this file")
        headers['instrume'] = ("G-CLEF_AIT",        "instrument name")
        headers['timesys']  = ("UTC",               "time coordinate system")
        headers['timeunit'] = ("s",                 "time unit")
        return headers