import asyncio
import tkinter as tk

from zaber_motion import Units
from zaber_motion.exceptions import ConnectionFailedException

from devices.MightexBufCmos import Camera
from devices.ZaberAdapter import ZaberAdapter
from functions.focus import Focuser

from .camera_panel import CameraPanel
from .function_panel import FunctionPanel
from .motion_panel import MotionPanel


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self, run_now : bool = True):
        """Main graphical application

        run_now: True to start loop immediately
        """
        super().__init__()

        # task variables
        self.loop = asyncio.get_event_loop()
        self.interval = 1/60 # in seconds
        self.tasks : list[asyncio.Task] = []

        # UI variables and setup
        self.default_padding = "3 3 12 12"
        self.title("Detector Stage Control")
        self.grid()
        self.configure(padx=10, pady=10)

        self.create_devices()
        self.make_panels()
        self.create_tasks()

        if run_now:
            self.run()

    def create_devices(self):
        """Create device handles"""
        self.camera = self.init_camera()
        self.z_motion = self.init_zaber()
        
    def init_camera(self) -> Camera|None:
        """Initialize connection to camera"""
        try:
            return Camera()
        except ValueError as e:
            print(e)
            return None

    def init_zaber(self) -> ZaberAdapter|None:
        """Initialize connection to Zaber stages"""

        axis_names = {"focal_x" : (33938, 1),
                      "focal_y" : (33937, 1),
                      "focal_z" : (33939, 1),
                      "cfm2_x"  : (110098, 1),
                      "cfm2_y"   : (113059, 1)}
        
        try:
            z_motion = ZaberAdapter(["/dev/ttyUSB0", "/dev/ttyUSB1"], axis_names)
        except ConnectionFailedException as e:
            print(e.message)
            return None
        
        # special limits
        # limit detector z-axis to 15mm
        z_motion.set_axis_setting(33939, 1, "limit.max", 15, Units.LENGTH_MILLIMETRES)

        return z_motion

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.camera)
        self.camera_panel.grid(column=0, row=0, columnspan=2)

        self.motion_panel = MotionPanel(self, self.z_motion)
        self.motion_panel.grid(column=0, row=1)

        axis = self.z_motion.axes["focal_z"] if self.z_motion else None
        self.function_panel = FunctionPanel(self, Focuser(self.camera, axis))
        self.function_panel.grid(column=1, row=1)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding=self.default_padding) # type: ignore

    def create_tasks(self):
        """Start cyclic update loops"""
        self.protocol("WM_DELETE_WINDOW", self.close) # bind close
        for panel in [self, self.camera_panel, self.motion_panel, self.function_panel]:
            self.tasks.append(self.loop.create_task(panel.update_loop(self.interval)))

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
        self.loop.stop()
        self.destroy()