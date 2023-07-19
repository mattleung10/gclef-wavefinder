import asyncio
import tkinter as tk

from zaber_motion.exceptions import ConnectionFailedException

from devices.Axis import Axis
from devices.MightexBufCmos import Camera
from devices.ZaberAdapter import ZaberAdapter
from functions.focus import Focuser
from functions.position import Positioner

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
        self.title("Red AIT Data Acquisition")
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
        zaber_adapter = self.init_zaber()
        self.axes : dict[str,Axis] = {}
        if zaber_adapter:
            self.axes.update(zaber_adapter.get_axes())

        # TODO
        # special limits
        # limit detector z-axis to 15mm
        # z_axis = self.axes["focal_z"] if self.axes else None
        # if z_axis:
        #     z_axis.set_limits(0, 15)
        
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
                      "cfm2_y"  : (113059, 1)}
        
        try:
            z_motion = ZaberAdapter(["/dev/ttyUSB0", "/dev/ttyUSB1"], axis_names)
        except ConnectionFailedException as e:
            print(e.message)
            return None

        return z_motion

    def make_functions(self):
        """Make function units"""
        z_axis = self.axes["focal_z"] if self.axes else None
        x_axis = self.axes["focal_x"] if self.axes else None
        y_axis = self.axes["focal_y"] if self.axes else None

        self.focuser = Focuser(self.camera, z_axis, steps=10, min_move=0.001)
        self.positioner = Positioner(self.camera, x_axis, y_axis, px_size=(3.75, 3.75))

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.camera)
        # internal frames of camera panel manage their own grid

        self.motion_panel = MotionPanel(self, self.axes)
        self.motion_panel.grid(column=0, row=1, sticky=tk.NSEW)
        
        self.function_panel = FunctionPanel(self, focuser=self.focuser, positioner=self.positioner)
        self.function_panel.grid(column=1, row=1, sticky=tk.NSEW)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding="3 3 12 12") # type: ignore
            f.grid_configure(padx=3, pady=12)

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
        # stop all panel sub-tasks
        self.motion_panel.close()
        self.function_panel.close()
        self.loop.stop()
        self.destroy()