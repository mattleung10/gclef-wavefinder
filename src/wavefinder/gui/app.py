import asyncio
import ctypes
import platform
import sys
import tkinter as tk
import traceback

from ..devices.Axis import Axis
from ..devices.GalilAdapter import GalilAdapter
from ..devices.MightexBufCmos import Camera
from ..devices.ZaberAdapter import ZaberAdapter
from ..functions.focus import Focuser
from ..functions.position import Positioner
from ..functions.writer import DataWriter
from .camera_panel import CameraPanel
from .config import Configuration
from .function_panel import FunctionPanel
from .motion_panel import MotionPanel
from .utils import Cyclic, make_task


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self, config_filename="config.toml"):
        """Main graphical application

        config_filename: filename of configuration
        """

        # For Windows, we need to set the DPI awareness so it looks right
        if "Windows".casefold() in platform.platform().casefold():
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore

        super().__init__()

        # config
        self.config = Configuration(config_filename)

        # task variables
        self.loop = asyncio.get_event_loop()
        self.tasks: set[asyncio.Task] = set()
        self.cyclics: set[Cyclic] = set()

        # UI variables and setup
        self.title("G-CLEF Wavefinder")
        self.grid()
        self.configure(padx=10, pady=10)

        self.create_devices()
        self.make_functions()
        self.make_panels()
        self.create_tasks()
        self.run()

    def create_devices(self):
        """Create device handles"""

        # camera
        try:
            self.camera = Camera(
                run_mode=self.config.camera_run_mode,
                bits=self.config.camera_bits,
                freq_mode=self.config.camera_freq_mode,
                resolution=self.config.camera_resolution,
                bin_mode=self.config.camera_bin_mode,
                nBuffer=self.config.camera_nBuffer,
                exposure_time=self.config.camera_exposure_time,
                fps=self.config.camera_fps,
                gain=self.config.camera_gain,
            )
        except ValueError as e:
            print(e)
            self.camera = None

        # motion axes
        self.axes: dict[str, Axis] = {}
        self.zaber_adapter = ZaberAdapter(
            self.config.zaber_ports, self.config.zaber_axis_names
        )
        self.axes.update(self.zaber_adapter.axes)
        self.galil_adapter = GalilAdapter(
            self.config.galil_address,
            self.config.galil_axis_names,
            self.config.galil_acceleration,
            self.config.galil_deceleration,
            self.config.galil_move_speed,
            self.config.galil_home_speed,
            self.config.galil_encoder_counts_per_degree,
            self.config.galil_drive_counts_per_degree,
        )
        self.axes.update(self.galil_adapter.axes)

        # set motion limits
        for axis_name, limits in self.config.motion_limits.items():
            axis = self.axes.get(axis_name, None)
            if axis:
                make_task(
                    axis.set_limits(low_limit=limits["min"], high_limit=limits["max"]),
                    self.tasks,
                )

        # add devices to cyclic tasks
        # NOTE self.camera may be None if camera is not found, so only add it if not None
        if self.camera:
            self.cyclics.add(self.camera)
        self.cyclics.update([self.zaber_adapter, self.galil_adapter])

    def make_functions(self):
        """Make function units"""

        x_axis = self.axes.get(self.config.camera_x_axis, None)
        y_axis = self.axes.get(self.config.camera_y_axis, None)
        z_axis = self.axes.get(self.config.focus_axis, None)

        self.positioner = Positioner(
            self.config, self.camera, x_axis, y_axis, px_size=self.config.pixel_size
        )
        self.focuser = Focuser(
            self.config,
            self.camera,
            z_axis,
            self.config.focus_points_per_pass,
            self.config.focus_frames_per_point,
            self.config.focus_minimum_move,
        )
        self.writer = DataWriter(
            self.config, self.camera, self.axes, self.positioner, self.focuser
        )

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.config, self.camera, self.writer)
        # internal frames of camera panel manage their own grid

        self.motion_panel = MotionPanel(self, self.axes)
        self.motion_panel.grid(column=0, row=1, sticky=tk.NSEW)

        self.function_panel = FunctionPanel(
            self, focuser=self.focuser, positioner=self.positioner
        )
        self.function_panel.grid(column=1, row=1, sticky=tk.NSEW)

        # pad all panels
        for f in self.winfo_children():
            f.configure(padding="3 3 12 12")  # type: ignore
            f.grid_configure(padx=3, pady=(10, 0))

        # add panels to cyclic tasks
        self.cyclics.update([self.camera_panel, self.motion_panel, self.function_panel])

    def create_tasks(self):
        """Start cyclic update loops

        These will run forever.
        """
        make_task(self.update_loop(self.config.interval), self.tasks, self.loop)
        for u in self.cyclics:
            make_task(u.update_loop(self.config.interval), self.tasks, self.loop)

    def run(self):
        """Run the loop"""
        print("--- Starting Application ---")
        self.protocol("WM_DELETE_WINDOW", self.close)  # bind close
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.close()
            traceback.print_exc(file=sys.stdout)

    async def update_loop(self, interval):
        """Update self in a loop"""
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        """Close application"""
        for u in self.cyclics:
            u.close()
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()
