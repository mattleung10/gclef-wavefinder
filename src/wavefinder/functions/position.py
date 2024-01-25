import numpy as np
from ..devices.Axis import Axis
from ..gui.config import Configuration


class Positioner:
    def __init__(
        self,
        config: Configuration,
        x_axis: Axis | None,
        y_axis: Axis | None,
    ) -> None:
        """General-purpose positioner

        config: application configuration
        x_axis: device that moves the image in the x direction
        y_axis: device that moves the image in the y direction
        """
        self.config = config
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.px_size = config.camera_pixel_size

        if not self.x_axis:
            print("Camera positioner x-axis not found.")
        if not self.y_axis:
            print("Camera positioner y-axis not found.")

    async def center(
        self, image_size: tuple[int, int], centroid: tuple[float, float]
    ) -> tuple[float, float]:
        """Move the x and y axes to center the centroid

        X is mirrored. Dones nothing if centroid is NaN.

        Args:
            image_size: tuple of (int, int) giving the size of the image
            centroid: tuple of (float, float) giving the computed centroid of the image

        Returns center position in mm
        """

        center = (0, 0)
        if self.x_axis and self.y_axis and not np.isnan(centroid).any():
            img_center = (image_size[0] / 2, image_size[1] / 2)
            move_x_px = -(centroid[0] - img_center[0])
            move_y_px = centroid[1] - img_center[1]

            await self.x_axis.move_relative((move_x_px * self.px_size[0]) / 1000)
            await self.y_axis.move_relative((move_y_px * self.px_size[1]) / 1000)

            center = (self.x_axis.position, self.y_axis.position)
        return center
