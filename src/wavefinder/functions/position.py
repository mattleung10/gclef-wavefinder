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
        px_size: pixel size as (x, y) in micrometers
        """
        self.config = config
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.px_size = config.camera_pixel_size

        if not self.x_axis:
            print("Camera positioner x-axis not found.")
        if not self.y_axis:
            print("Camera positioner y-axis not found.")

    async def center(self) -> tuple[float, float]:
        """Move the x and y axes to center the centroid

        X is mirrored.

        Returns center position in mm
        """

        center = (0, 0)
        if self.x_axis and self.y_axis:
            img_center = (
                self.config.image_size[0] / 2,
                self.config.image_size[1] / 2,
            )
            move_x_px = -(self.config.image_centroid[0] - img_center[0])
            move_y_px = self.config.image_centroid[1] - img_center[1]

            await self.x_axis.move_relative((move_x_px * self.px_size[0]) / 1000)
            await self.y_axis.move_relative((move_y_px * self.px_size[1]) / 1000)

            center = (self.x_axis.position, self.y_axis.position)
        return center
