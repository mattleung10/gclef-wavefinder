# import numpy as np
from PIL import Image

from devices.MightexBufCmos import Camera
from devices.Axis import Axis
from functions.image import get_centroid_and_variance


class Positioner:
    def __init__(self,
                 camera : Camera|None,
                 x_axis : Axis|None,
                 y_axis : Axis|None,
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

    async def center(self):
        """Move the x and y axes to center the centroid
        
        X is mirrored.
        """

        if self.camera and self.x_axis and self.y_axis:
            img = Image.fromarray(self.camera.get_newest_frame().img)
            stats = get_centroid_and_variance(img)
            img_center = ((img.size[0] - 1) / 2, (img.size[1] - 1) / 2)
            move_x_px = -(stats[0] - img_center[0])
            move_y_px =   stats[1] - img_center[1]

            await self.x_axis.move_relative(move_x_px * self.px_size[0])
            await self.y_axis.move_relative(move_y_px * self.px_size[1])