import tkinter as tk
from tkinter import ttk

from zaber_motion.ascii import Connection
from zaber_motion.exceptions import ConnectionFailedException

from devices.MightexBufCmos import Camera

from .camera_panel import CameraPanel
from .detector_motion_panel import DetectorMotionPanel


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self):
        super().__init__()
        self.title("Detector Stage Control")
        self.grid()

        self.view_delay = 1000 // 60 # 60 Hz
        self.default_padding = "3 3 12 12"

        self.create_devices()
        self.make_frames()
        self.start_update_loops()

    def create_devices(self):
        """Create device handles"""
        try:
            self.camera = Camera()
        except ValueError as e:
            print(e)
            self.camera = None

        try:
            SN_X = 33938
            SN_Y = 33937
            SN_Z = 33939

            zaber_con = Connection.open_serial_port("/dev/ttyUSB0")
            zaber_con.enable_alerts()

            device_list = zaber_con.detect_devices()
            det_stage_x = next(filter(lambda d: d.serial_number == SN_X, device_list))
            det_stage_y = next(filter(lambda d: d.serial_number == SN_Y, device_list))
            det_stage_z = next(filter(lambda d: d.serial_number == SN_Z, device_list))

            self.det_ax = det_stage_x.get_axis(1)
            self.det_ay = det_stage_y.get_axis(1)
            self.det_az = det_stage_z.get_axis(1)
        except ConnectionFailedException as e:
            print(e)
            self.det_ax = None
            self.det_ay = None
            self.det_az = None

    def make_frames(self):
        """Make view frames"""

        self.camera_panel = CameraPanel(self, self.camera, self.view_delay)
        self.camera_panel.grid(column=0, row=0)

        self.detector_motion_panel = DetectorMotionPanel(self, self.det_ax, self.det_ay, self.det_az)
        self.detector_motion_panel.grid(column=0, row=1)

        # pad them all
        for f in self.winfo_children():
            f.configure(padding=self.default_padding) # type: ignore


    def start_update_loops(self):
        """Start cyclic update loops"""
        self.camera_panel.after(self.view_delay, self.camera_panel.update)

