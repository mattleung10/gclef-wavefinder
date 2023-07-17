# import numpy as np
from PIL import Image
from zaber_motion import Units

from devices.MightexBufCmos import Camera
from devices.ZaberAdapter import ZaberAxis
from functions.image import get_centroid_and_variance


class Positioner:
    def __init__(self,
                 camera : Camera|None,
                 x_axis : ZaberAxis|None,
                 y_axis : ZaberAxis|None,
                 px_size: tuple[float,float]) -> None:
        """General-purpose positioner
        
        camera: MightexBufCmos Camera device
        x_axis: device that moves the image in the x direction
        y_axis: device that moves the image in the y direction
        px_size: pixel size as (x, y) in micrometers
        """
        self.camera = camera
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.px_size = px_size

    def center(self):
        """Move the x and y axes to center the centroid"""

        if self.camera and self.x_axis and self.y_axis:
            img = Image.fromarray(self.camera.get_newest_frame().img)
            stats = get_centroid_and_variance(img)
            img_center = ((img.size[0] - 1) / 2, (img.size[1] - 1) / 2)
            move_x_px = stats[0] - img_center[0]
            move_y_px = stats[1] - img_center[1]

            self.x_axis.axis.move_relative(move_x_px * self.px_size[0],
                                        Units.LENGTH_MICROMETRES,
                                        wait_until_idle=False)
            self.x_axis.status = ZaberAxis.MOVING
            self.y_axis.axis.move_relative(move_y_px * self.px_size[1],
                                        Units.LENGTH_MICROMETRES,
                                        wait_until_idle=False)
            self.y_axis.status = ZaberAxis.MOVING