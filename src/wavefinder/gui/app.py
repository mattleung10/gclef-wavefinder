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


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self, run_now: bool = True):
        """Main graphical application

        run_now: True to start loop immediately
        """
        
        # For Windows, we need to set the DPI awareness so it looks right
        if "Windows".casefold() in platform.platform().casefold():
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        
        super().__init__()

        # task variables
        self.loop = asyncio.get_event_loop()
        self.interval = 1/60 # in seconds
        self.tasks: set[asyncio.Task] = set()

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
        self.zaber_adapter = self.init_zaber()
        self.galil_adapter = self.init_galil()
        self.axes: dict[str, Axis] = {}
        self.axes.update(self.zaber_adapter.axes)
        self.axes.update(self.galil_adapter.axes)

        # special limits
        # TODO add all limits
        # limit detector z-axis to 15mm
        z_axis = self.axes.get("focal_z", None)
        if z_axis:
            t = self.loop.create_task(z_axis.set_limits(None, 15.0))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)
        # limit gimbal_1_el to (-10, 10)
        gimbal_1_el = self.axes.get("gimbal_1_el", None)
        if gimbal_1_el:
            t = self.loop.create_task(gimbal_1_el.set_limits(-10, 10))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)
        
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
        
        zaber = ZaberAdapter(["/dev/ttyUSB0", "/dev/ttyUSB1"], zaber_axis_names)
        return zaber
    
    def init_galil(self) -> GalilAdapter:
        """Initialize connection to Galil stages"""

        galil_axis_names = {"gimbal_1_el": "A",
                            "gimbal_1_az": "B",
                            "gimbal_2_el": "C",
                            "gimbal_2_az": "D"}
        
        galil = GalilAdapter("192.168.1.19", galil_axis_names)
        return galil
        
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

        self.motion_panel = MotionPanel(self, self.axes)
        self.motion_panel.grid(column=0, row=1, sticky=tk.NSEW)
        
        self.function_panel = FunctionPanel(self, focuser=self.focuser,
                                            positioner=self.positioner)
        self.function_panel.grid(column=1, row=1, sticky=tk.NSEW)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding="3 3 12 12") # type: ignore
            f.grid_configure(padx=3, pady=12)

    def create_tasks(self):
        """Start cyclic update loops
        
        These will run forever.
        """
        self.protocol("WM_DELETE_WINDOW", self.close) # bind close
        for panel in [self, self.camera_panel, self.motion_panel, self.function_panel]:
            self.tasks.add(self.loop.create_task(panel.update_loop(self.interval)))
        for interface in [self.zaber_adapter, self.galil_adapter]:
            self.tasks.add(self.loop.create_task(interface.update_loop(self.interval)))

    def run(self):
        """Run the loop"""
        print("--- Starting Application ---")
        self.loop.run_forever()

    async def update_loop(self, interval):
        """Update self in a loop"""
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        """Close application"""
        for task in self.tasks:
            task.cancel()
        self.galil_adapter.close()
        # stop all panel sub-tasks
        self.motion_panel.close()
        self.function_panel.close()
        self.loop.stop()
        self.destroy()