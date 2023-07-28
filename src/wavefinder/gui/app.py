import asyncio
import ctypes
import platform
import tkinter as tk

from ..devices.Axis import Axis
from ..devices.GalilAdapter import GalilAdapter
from ..devices.MightexBufCmos import Camera
from ..devices.ZaberAdapter import ZaberAdapter
from ..functions.focus import Focuser
from ..functions.position import Positioner
from .camera_panel import CameraPanel
from .function_panel import FunctionPanel
from .motion_panel import MotionPanel
from .utils import make_task


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self, run_now: bool = True):
        """Main graphical application

        run_now: True to start loop immediately
        """
        
        # For Windows, we need to set the DPI awareness so it looks right
        if "Windows".casefold() in platform.platform().casefold():
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # type: ignore
        
        super().__init__()

        # task variables
        self.loop = asyncio.get_event_loop()
        self.interval = 1/60 # in seconds
        self.tasks: set[asyncio.Task] = set()
        self.updaters: set = set()

        # UI variables and setup
        self.title("G-CLEF Wavefinder")
        self.grid()
        self.configure(padx=10, pady=10)

        self.create_devices()
        self.make_functions()
        self.make_panels()
        self.create_tasks()

        if run_now:
            self.run()

    def create_devices(self):
        """Create device handles"""
        self.camera = self.init_camera()
        self.updaters.add(self.camera)

        self.zaber_adapter = self.init_zaber()
        self.updaters.add(self.zaber_adapter)

        self.galil_adapter = self.init_galil()
        self.updaters.add(self.galil_adapter)

        self.axes: dict[str, Axis] = {}
        self.axes.update(self.zaber_adapter.axes)
        self.axes.update(self.galil_adapter.axes)

        # motion limits
        limit_map = {"focal_z": (None, 15.0),
                     "cfm1_az": (-10.0, 10.0),
                     "cfm1_el": (-10.0, 10.0),
                     "cfm2_az": (-10.0, 10.0),
                     "cfm2_el": (-10.0, 10.0)}
        self.set_motion_limits(limit_map)
        
    def init_camera(self) -> Camera | None:
        """Initialize connection to camera"""
        try:
            return Camera()
        except ValueError as e:
            print(e)
            return None

    def init_zaber(self) -> ZaberAdapter:
        """Initialize connection to Zaber stages"""

        zaber_axis_names = {"focal_x": (33938, 1),
                            "focal_y": (33937, 1),
                            "focal_z": (33939, 1),
                            "cfm2_x" : (110098, 1),
                            "cfm2_y" : (113059, 1)}
        
        # TODO: put full list back
        # zaber = ZaberAdapter(["COM1", "COM2", "COM3", "COM4", "COM5",
        #                       "COM6", "COM7", "COM8", "COM9", "COM10",
        #                       "/dev/ttyUSB0", "/dev/ttyUSB1",
        #                       "/dev/ttyUSB2", "/dev/ttyUSB3"], zaber_axis_names)
        zaber = ZaberAdapter(["COM3", "COM6"], zaber_axis_names)
        return zaber
    
    def init_galil(self) -> GalilAdapter:
        """Initialize connection to Galil stages"""

        galil_axis_names = {"cfm1_az": "A",
                            "cfm1_el": "B",
                            "cfm2_az": "C",
                            "cfm2_el": "D"}
        
        galil = GalilAdapter("192.168.1.19", galil_axis_names)
        return galil

    def set_motion_limits(self, limit_map: dict[str, tuple[float|None, float|None]]):
        """Set motion limits for all axes
        
        Args:
            limit_map: map of axis name to limit tuple, e.g. {"cfm1_az": (-10.0, 10.0)}
        """
        for axis_name, limits in limit_map.items():
            axis = self.axes.get(axis_name, None)
            if axis:
                make_task(axis.set_limits(*limits), self.tasks)

    def make_functions(self):
        """Make function units"""
        z_axis = self.axes.get("focal_z", None)
        x_axis = self.axes.get("focal_x", None)
        y_axis = self.axes.get("focal_y", None)

        self.focuser = Focuser(self.camera, z_axis, steps=10, min_move=0.001)
        self.positioner = Positioner(self.camera, x_axis, y_axis, px_size=(3.75, 3.75))

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.camera)
        # internal frames of camera panel manage their own grid
        self.updaters.add(self.camera_panel)

        self.motion_panel = MotionPanel(self, self.axes)
        self.motion_panel.grid(column=0, row=1, sticky=tk.NSEW)
        self.updaters.add(self.motion_panel)
        
        self.function_panel = FunctionPanel(self, focuser=self.focuser,
                                            positioner=self.positioner)
        self.function_panel.grid(column=1, row=1, sticky=tk.NSEW)
        self.updaters.add(self.function_panel)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding="3 3 12 12") # type: ignore
            f.grid_configure(padx=3, pady=12)

    def create_tasks(self):
        """Start cyclic update loops
        
        These will run forever.
        """
        make_task(self.update_loop(self.interval), self.tasks, self.loop)
        for u in self.updaters:
            if u:
                make_task(u.update_loop(self.interval), self.tasks, self.loop)

    def run(self):
        """Run the loop"""
        print("--- Starting Application ---")
        self.protocol("WM_DELETE_WINDOW", self.close) # bind close
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.close()

    async def update_loop(self, interval):
        """Update self in a loop"""
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        """Close application"""
        for u in self.updaters:
            if u:
                u.close()
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()