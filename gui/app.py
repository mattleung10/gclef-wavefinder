import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.ascii import Axis, Connection
from zaber_motion.exceptions import ConnectionFailedException

from devices.MightexBufCmos import Camera

from focus import Focuser
from .camera_panel import CameraPanel
from .motion_panel import MotionPanel
from .function_panel import FunctionPanel

class App(tk.Tk):
    """Main graphical application"""

    def __init__(self):
        super().__init__()

        self.view_delay = 1000 // 60 # 60 Hz
        self.default_padding = "3 3 12 12"
        
        self.title("Detector Stage Control")
        self.grid()
        self.configure(padx=10, pady=10)
        self.create_devices()
        self.make_panels()
        self.start_update_loops()

    def create_devices(self):
        """Create device handles"""
        self.camera = self.init_camera()
        self.det_ax, self.det_ay, self.det_az = self.init_zaber()
        
    def init_camera(self) -> Camera|None:
        """Initialize connection to camera"""
        try:
            return Camera()
        except ValueError as e:
            print(e)
            return None

    def init_zaber(self) -> tuple[Axis|None, Axis|None, Axis|None]:
        """Initialize connection to Zaber stages"""

        SN_DET_X = 33938
        SN_DET_Y = 33937
        SN_DET_Z = 33939

        axes : dict[int, Axis|None] = {SN_DET_X: None,
                                       SN_DET_Y: None,
                                       SN_DET_Z: None}
        
        try:
            print("Connecting to Zaber stages... ", end='')
            zaber_con = Connection.open_serial_port("/dev/ttyUSB0")
            zaber_con.enable_alerts()
            print("connected!")

            device_list = zaber_con.detect_devices()
            for sn in axes.keys():
                try:
                    print("Finding serial# " + str(sn) + "... ", end='')
                    device = next(filter(lambda d: d.serial_number == sn, device_list), None)
                    if device:
                        axes[sn] = device.get_axis(1)
                        print("OK!")
                except Exception as e:
                    print(e)
        except ConnectionFailedException as e:
            print(e.message)

        # special limits
        # limit detector z-axis to 15mm
        az = axes[SN_DET_Z]
        if az:
            az.settings.set(setting="limit.max", value=15, unit=Units.LENGTH_MILLIMETRES)
        return (axes[SN_DET_X], axes[SN_DET_Y], axes[SN_DET_Z])

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.camera, self.view_delay)
        self.camera_panel.grid(column=0, row=0, columnspan=2)

        self.motion_panel = MotionPanel(self, self.det_ax, self.det_ay,
                                        self.det_az, self.view_delay)
        self.motion_panel.grid(column=0, row=1)

        self.function_panel = FunctionPanel(self, Focuser(self.camera, self.det_az),
                                            self.view_delay)
        self.function_panel.grid(column=1, row=1)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding=self.default_padding) # type: ignore

    def start_update_loops(self):
        """Start cyclic update loops"""
        self.camera_panel.update()
        self.motion_panel.update()
        self.function_panel.update()
