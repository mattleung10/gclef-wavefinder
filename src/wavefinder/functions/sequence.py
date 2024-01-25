import tkinter as tk

import numpy as np

from ..devices.Axis import Axis
from ..devices.MightexBufCmos import Camera
from ..gui.config import Configuration
from .image import find_full_width_half_max, threshold_copy


class Sequencer:
    def __init__(
        self, config: Configuration, camera: Camera | None, axes: dict[str, Axis]
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
        """
        self.config = config
        self.sequence: list[dict[str, float]] = list()
        self.axes = axes

    async def focus(self) -> float:
        return np.nan
    
    async def center(
        self, image_size: tuple[int, int], centroid: tuple[float, float]
    ) -> tuple[float, float]:
        return (np.nan, np.nan)

    def read_input_file(self, filename: str):
        """Read input sequence file

        Args:
            filename: path to filename
        """
        with open(filename) as f:
            # reset the sequence
            self.sequence = list()
            # set headers, strip whitespace from header names
            header_line = f.readline()
            headers = [h.strip() for h in header_line.split(",")]

            # this loop will start with the 2nd line because the previous
            # readline has advanced the buffer's iterator0
            for line in f:
                # make a dict, using the header values
                d: dict[str, float] = {}
                for i, n in enumerate(line.split(",")):
                    d[headers[i]] = float(n)
                self.sequence.append(d)

    async def run_sequence(self, output_dir: str, status_text: tk.StringVar):
        """Run sequence and store data in output directory

        Args:
            output_dir: path to output directory
            status_text: Tk StringVar to update with status
        """

        # TODO set camera to trigger mode
        # old_mode = self.camera.run_mode
        # await self.camera.set_mode(run_mode=Camera.TRIGGER, write_now=True)

        for i, row in enumerate(self.sequence):
            print(self.axes)
            # 1) move to position
            for col in row:
                # match header with motion axis, then move to position
                a = self.axes.get(col)
                if a:
                    await a.move_absolute(row[col])
            # 2) center image
            # TODO: clear buffer, take image
