import asyncio
import ctypes
import platform
import sys
import tkinter as tk
import traceback
import tomllib

from ..devices.Axis import Axis
from ..devices.GalilAdapter import GalilAdapter
from ..devices.MightexBufCmos import Camera
from ..devices.ZaberAdapter import ZaberAdapter
from ..functions.focus import Focuser
from ..functions.position import Positioner
from .camera_panel import CameraPanel
from .function_panel import FunctionPanel
from .motion_panel import MotionPanel
from .utils import Cyclic, make_task


class App(tk.Tk):
    """Main graphical application"""

    def __init__(self, config_file="config.toml"):
        """Main graphical application

        config_file: filename of configuration
        """

        # For Windows, we need to set the DPI awareness so it looks right
        if "Windows".casefold() in platform.platform().casefold():
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # type: ignore

        super().__init__()

        # config
        self.default_config()
        self.set_config(config_file)

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

    def set_config(self, config_file: str):
        """Set config

        Args
            config_file: name of config file
        """
        params = None
        try:
            with open(config_file, "rb") as f:
                params = tomllib.load(f)
                print(params) #TODO remove
        except FileNotFoundError as e:
            print(f"Can't find config file {e.filename}, using defaults")
            return
        except tomllib.TOMLDecodeError as e:
            print(f"Error loading config file {config_file}, using defaults\n{e}")
            return

        try:
            if "app" in params:
                if "update_rate" in params["app"]:
                    self.interval = params["app"]["update_rate"]
            if "camera" in params:
                if "run_mode" in params["camera"]:
                    if params["camera"]["run_mode"] == "NORMAL":
                        self.camera_run_mode = Camera.NORMAL
                    elif params["camera"]["run_mode"] == "TRIGGER":
                        self.camera_run_mode = Camera.TRIGGER
                if "bits" in params["camera"]:
                    if params["camera"]["bits"] == 8:
                        self.camera_bits = 8
                    elif params["camera"]["bits"] == 12:
                        self.camera_bits = 12
                if "freq_mode" in params["camera"]:
                    if params["camera"]["freq_mode"] in range(5):
                        self.camera_freq_mode = params["camera"]["freq_mode"]
                if "resolution" in params["camera"]:
                    if "rows" in params["camera"]["resolution"]:
                        r = params["camera"]["resolution"]["rows"]
                        if "columns" in params["camera"]["resolution"]:
                            c = params["camera"]["resolution"]["columns"]
                            if r in range(1280) and c in range(960):
                                self.camera_resolution = (r, c)
                if "bin_mode" in params["camera"]:
                    if params["camera"]["bin_mode"] == "NO_BIN":
                        self.camera_bin_mode = Camera.NO_BIN
                    elif params["camera"]["bin_mode"] == "BIN1X2":
                        self.camera_bin_mode = Camera.BIN1X2
                    elif params["camera"]["bin_mode"] == "BIN1X3":
                        self.camera_bin_mode = Camera.BIN1X3
                    elif params["camera"]["bin_mode"] == "BIN1X4":
                        self.camera_bin_mode = Camera.BIN1X4
                    elif params["camera"]["bin_mode"] == "SKIP":
                        self.camera_bin_mode = Camera.SKIP
                if "nBuffer" in params["camera"]:
                    if params["camera"]["nBuffer"] in range(25):
                        self.camera_nBuffer = params["camera"]["nBuffer"]
                # TODO rest of params
        except Exception as e:
            print(f"Error parsing config file {config_file}, dying!\n{e}")
            self.close()
            exit(1)

    def default_config(self):
        # task defaults
        self.interval = 1/60 # seconds

        # camera defaults
        self.camera_run_mode = Camera.NORMAL
        self.camera_bits = 8
        self.camera_freq_mode = 0
        self.camera_resolution = (1280, 960)
        self.camera_bin_mode = Camera.NO_BIN
        self.camera_nBuffer = 24
        self.camera_exposure_time = 50
        self.camera_fps = 10
        self.camera_gain = 15
        self.pixel_size = (3.75, 3.75)

        # motion defaults
        self.zaber_ports = ["COM1", "COM2", "COM3", "COM4", "COM5",
                            "COM6", "COM7", "COM8", "COM9", "COM10",
                            "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyUSB3"]
        self.galil_address = "192.168.1.19"
        self.zaber_axis_names = {"focal_x": 33938,
                                 "focal_y": 33937,
                                 "focal_z": 33939,
                                 "cfm2_x" : 110098,
                                 "cfm2_y" : 113059}
        self.galil_axis_names = {"cfm1_az": "A",
                                 "cfm1_el": "B",
                                 "cfm2_az": "C",
                                 "cfm2_el": "D"}
        self.galil_acceleration = 2000000
        self.galil_deceleration = 2000000
        self.galil_move_speed = 100000
        self.galil_home_speed = 5000
        self.galil_encoder_counts_per_degree = 800
        self.galil_drive_counts_per_degree = 10000
        self.motion_limits = {"focal_z": (None, 15.0),
                              "cfm1_az": (-10.0, 10.0),
                              "cfm1_el": (-10.0, 10.0),
                              "cfm2_az": (-10.0, 10.0),
                              "cfm2_el": (-10.0, 10.0)}

        # positioner defaults
        self.camera_x_axis = "focal_x"
        self.camera_y_axis = "focal_y"

        # focuser defaults
        self.focus_axis = "focal_z"
        self.focus_points_per_pass = 10
        self.focus_frames_per_point = 3
        self.focus_minimum_move = 0.001

    def create_devices(self):
        """Create device handles"""

        # camera
        try:
            self.camera = Camera(run_mode=self.camera_run_mode,
                                 bits=self.camera_bits,
                                 freq_mode=self.camera_freq_mode,
                                 resolution=self.camera_resolution,
                                 bin_mode=self.camera_bin_mode,
                                 nBuffer=self.camera_nBuffer,
                                 exposure_time=self.camera_exposure_time,
                                 fps=self.camera_fps,
                                 gain=self.camera_gain)
        except ValueError as e:
            print(e)
            self.camera = None

        # motion axes
        self.axes: dict[str, Axis] = {}
        self.zaber_adapter = ZaberAdapter(self.zaber_ports, self.zaber_axis_names)
        self.axes.update(self.zaber_adapter.axes)
        self.galil_adapter = GalilAdapter(self.galil_address, self.galil_axis_names,
                                          self.galil_acceleration, self.galil_deceleration,
                                          self.galil_move_speed, self.galil_home_speed,
                                          self.galil_encoder_counts_per_degree,
                                          self.galil_drive_counts_per_degree)
        self.axes.update(self.galil_adapter.axes)

        # set motion limits
        for axis_name, limits in self.motion_limits.items():
            axis = self.axes.get(axis_name, None)
            if axis:
                make_task(axis.set_limits(*limits), self.tasks)

        # add devices to cyclic tasks
        # NOTE self.camera may be None if camera is not found, so only add it if not None
        if self.camera:
            self.cyclics.add(self.camera)
        self.cyclics.update([self.zaber_adapter, self.galil_adapter])

    def make_functions(self):
        """Make function units"""

        x_axis = self.axes.get(self.camera_x_axis, None)
        y_axis = self.axes.get(self.camera_y_axis, None)
        z_axis = self.axes.get(self.focus_axis, None)

        self.positioner = Positioner(self.camera, x_axis, y_axis, px_size=self.pixel_size)
        self.focuser = Focuser(self.camera, z_axis, self.focus_points_per_pass,
                               self.focus_frames_per_point, self.focus_minimum_move)

    def make_panels(self):
        """Make UI panels"""
        self.camera_panel = CameraPanel(self, self.camera)
        # internal frames of camera panel manage their own grid

        self.motion_panel = MotionPanel(self, self.axes)
        self.motion_panel.grid(column=0, row=1, sticky=tk.NSEW)

        self.function_panel = FunctionPanel(self, focuser=self.focuser, positioner=self.positioner)
        self.function_panel.grid(column=1, row=1, sticky=tk.NSEW)

        # pad all panels
        for f in self.winfo_children():
            f.configure(padding="3 3 12 12") # type: ignore
            f.grid_configure(padx=3, pady=(10, 0))

        # add panels to cyclic tasks
        self.cyclics.update([self.camera_panel, self.motion_panel, self.function_panel])

    def create_tasks(self):
        """Start cyclic update loops

        These will run forever.
        """
        make_task(self.update_loop(self.interval), self.tasks, self.loop)
        for u in self.cyclics:
            make_task(u.update_loop(self.interval), self.tasks, self.loop)

    def run(self):
        """Run the loop"""
        print("--- Starting Application ---")
        self.protocol("WM_DELETE_WINDOW", self.close) # bind close
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