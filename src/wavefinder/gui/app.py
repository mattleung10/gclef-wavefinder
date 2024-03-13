import asyncio
import ctypes
import platform
import sys
import tkinter as tk
import traceback
from importlib.metadata import PackageNotFoundError, version

from ..devices.Axis import Axis
from ..devices.DkMonochromator import DkMonochromator
from ..devices.GalilAdapter import GalilAdapter
from ..devices.MightexBufCmos import Camera
from ..devices.ZaberAdapter import ZaberAdapter
from ..functions.sequence import Sequencer
from ..functions.writer import DataWriter
from .camera_panel import CameraPanel
from .config import Configuration
from .function_panel import FunctionPanel
from .monochrom_panel import MonochromPanel
from .motion_panel import MotionPanel
from .scrollable_container import ScrollableWindow
from .utils import Cyclic, make_task


class App(ScrollableWindow):
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

        # get version string and print intro
        try:
            self.config.version = version("wavefinder")
        except PackageNotFoundError:
            self.config.version = "?"
        print(f"--- G-CLEF Wavefinder v{self.config.version} ---")

        # UI setup
        self.title(f"G-CLEF Wavefinder v{self.config.version}")
        self.grid()

        # start application
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

        # monochromator
        self.dk = DkMonochromator(self.config.monochrom_port)

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
        # NOTE: self.camera may be None if camera is not found, so only add it if not None
        # TODO: instead of allowing camera to be None, add a "connected" parameter
        if self.camera:
            self.cyclics.add(self.camera)
        self.cyclics.update([self.dk, self.zaber_adapter, self.galil_adapter])

    def make_functions(self):
        """Make function units"""
        self.writer = DataWriter(self.camera, self.axes, self.dk)
        self.sequencer = Sequencer(
            self.config, self.camera, self.axes, self.dk, self.writer
        )

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self.frame, self.config, self.camera)
        # internal frames of camera panel manage their own grid

        self.monochrom_panel = MonochromPanel(self.frame, self.config, self.dk)
        self.monochrom_panel.grid(column=0, row=1, rowspan=2, sticky=tk.NSEW)

        self.motion_panel = MotionPanel(self.frame, self.axes)
        self.motion_panel.grid(column=0, row=3, sticky=tk.NSEW)

        self.function_panel = FunctionPanel(
            self.frame,
            self.config,
            camera=self.camera,
            sequencer=self.sequencer,
            data_writer=self.writer,
        )
        self.function_panel.grid(column=1, row=2, rowspan=2, sticky=tk.NSEW)

        # pad between all panels
        for f in self.frame.winfo_children():
            f.grid_configure(padx=3, pady=5, ipady=5, ipadx=3)

        # add panels to cyclic tasks
        self.cyclics.update(
            [
                self.camera_panel,
                self.monochrom_panel,
                self.motion_panel,
                self.function_panel,
            ]
        )

    def create_tasks(self):
        """Start cyclic update loops

        These will run forever.
        """
        make_task(self.update_loop(self.config.interval), self.tasks, self.loop)
        for u in self.cyclics:
            make_task(u.update_loop(self.config.interval), self.tasks, self.loop)

    def run(self):
        """Run the loop"""
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
