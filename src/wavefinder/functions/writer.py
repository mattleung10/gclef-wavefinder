import numpy as np
from astropy.io import fits

from PIL import Image
from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera


class DataWriter:
    def __init__(self, camera: Camera | None, axes: dict[str, Axis], positioner, focuser) -> None:
        self.camera = camera
        self.axes = axes

    def write_fits_file(self, filename: str, img: np.ndarray | None = None):
        """Write a FITS file using most recent image and telemetry
        
        Args:
            filename: name of fits file to be written
            img: write the given image if not None
        """

        hdu = fits.PrimaryHDU()

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
        
        hdu.header.update(self.make_axis_headers())
        hdu.header.update(self.make_general_headers())
        hdu.data = img
        hdu.writeto(filename, overwrite=True, output_verify='fix')

    def make_camera_frame_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.camera:
            headers['camera'] = self.camera.modelno
        return headers

    def make_dummy_frame_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        headers['camera'] = "dummy"
        return headers

    def make_axis_headers(self):
        pass

    def make_general_headers(self):
        pass