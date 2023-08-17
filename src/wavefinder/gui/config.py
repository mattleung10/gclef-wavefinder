
import tomllib

from ..devices.MightexBufCmos import Camera


class Configurable:
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
        self.zaber_axis_names = {"detector x":  {"sn": 33938,  "keyword": "detxpos"},
                                 "detector y":  {"sn": 33937,  "keyword": "detypos"},
                                 "detector z":  {"sn": 33939,  "keyword": "detzpos"},
                                 "cfm2 x":      {"sn": 110098, "keyword": "cfm2xpos"},
                                 "cfm2 y":      {"sn": 113059, "keyword": "cfm2ypos"}}
        self.galil_axis_names = {"cfm1 azimuth":    {"ch": "A", "keyword": "cfm1az"},
                                 "cfm1 elevation":  {"ch": "B", "keyword": "cfm1el"},
                                 "cfm2 azimuth":    {"ch": "C", "keyword": "cfm2az"},
                                 "cfm2 elevation":  {"ch": "D", "keyword": "cfm2el"}}
        self.galil_acceleration = 2000000
        self.galil_deceleration = 2000000
        self.galil_move_speed   =  100000
        self.galil_home_speed   =    5000
        self.galil_encoder_counts_per_degree = 800
        self.galil_drive_counts_per_degree = 10000
        self.motion_limits = {"detector z":     {"min":   0.0, "max": 15.0},
                              "cfm1 azimuth":   {"min": -30.0, "max": 30.0},
                              "cfm1 elevation": {"min": -30.0, "max": 30.0},
                              "cfm2 azimuth":   {"min": -30.0, "max": 30.0},
                              "cfm2 elevation": {"min": -30.0, "max": 30.0}}

        # positioner defaults
        self.camera_x_axis = "detector x"
        self.camera_y_axis = "detector y"

        # focuser defaults
        self.focus_axis = "detector z"
        self.focus_points_per_pass = 10
        self.focus_frames_per_point = 3
        self.focus_minimum_move = 0.001

    def set_config(self, config_file: str):
        """Set config

        Args
            config_file: name of config file
        """
        c = None
        try:
            with open(config_file, "rb") as f:
                c = tomllib.load(f)
        except FileNotFoundError as e:
            print(f"Can't find config file {e.filename}, using defaults")
            return
        except tomllib.TOMLDecodeError as e:
            print(f"Error loading config file {config_file}, using defaults\n{e}")
            return

        try:
            if "app" in c:
                if "update_rate" in c["app"]:
                    self.interval = c["app"]["update_rate"]
            if "camera" in c:
                if "run_mode" in c["camera"]:
                    if c["camera"]["run_mode"] == "NORMAL":
                        self.camera_run_mode = Camera.NORMAL
                    elif c["camera"]["run_mode"] == "TRIGGER":
                        self.camera_run_mode = Camera.TRIGGER
                if "bits" in c["camera"]:
                    if c["camera"]["bits"] == 8:
                        self.camera_bits = 8
                    elif c["camera"]["bits"] == 12:
                        self.camera_bits = 12
                if "freq_mode" in c["camera"]:
                    if c["camera"]["freq_mode"] in range(5):
                        self.camera_freq_mode = c["camera"]["freq_mode"]
                if "resolution" in c["camera"]:
                    if "rows" in c["camera"]["resolution"]:
                        rows = c["camera"]["resolution"]["rows"]
                        if "columns" in c["camera"]["resolution"]:
                            cols = c["camera"]["resolution"]["columns"]
                            if rows in range(1280) and cols in range(960):
                                self.camera_resolution = (rows, cols)
                if "bin_mode" in c["camera"]:
                    if c["camera"]["bin_mode"] == "NO_BIN":
                        self.camera_bin_mode = Camera.NO_BIN
                    elif c["camera"]["bin_mode"] == "BIN1X2":
                        self.camera_bin_mode = Camera.BIN1X2
                    elif c["camera"]["bin_mode"] == "BIN1X3":
                        self.camera_bin_mode = Camera.BIN1X3
                    elif c["camera"]["bin_mode"] == "BIN1X4":
                        self.camera_bin_mode = Camera.BIN1X4
                    elif c["camera"]["bin_mode"] == "SKIP":
                        self.camera_bin_mode = Camera.SKIP
                if "nBuffer" in c["camera"]:
                    if c["camera"]["nBuffer"] in range(25):
                        self.camera_nBuffer = c["camera"]["nBuffer"]
                if "exposure" in c["camera"]:
                    if isinstance(c["camera"]["exposure"], float):
                        self.camera_exposure_time = c["camera"]["exposure"]
                if "fps" in c["camera"]:
                    if isinstance(c["camera"]["fps"], float):
                        self.camera_fps = c["camera"]["fps"]
                if "gain" in c["camera"]:
                    if c["camera"]["gain"] in range(6,42):
                        self.camera_gain = c["camera"]["gain"]
            if "motion" in c:
                if "zaber" in c["motion"]:
                    if "ports" in c["motion"]["zaber"]:
                        if isinstance(c["motion"]["zaber"]["ports"], (list, str)):
                            self.zaber_ports = c["motion"]["zaber"]["ports"]
                    if "axis_names" in c["motion"]["zaber"]:
                        if isinstance(c["motion"]["zaber"]["axis_names"], dict):
                            self.zaber_axis_names = c["motion"]["zaber"]["axis_names"]
                if "galil" in c["motion"]:
                    if "address" in c["motion"]["galil"]:
                        if isinstance(c["motion"]["galil"]["address"], str):
                            self.galil_address = c["motion"]["galil"]["address"]
                    if "acceleration" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["acceleration"] > 0:
                            self.galil_acceleration = c["motion"]["galil"]["acceleration"]
                    if "deceleration" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["deceleration"] > 0:
                            self.galil_deceleration = c["motion"]["galil"]["deceleration"]
                    if "move_speed" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["move_speed"] > 0:
                            self.galil_move_speed = c["motion"]["galil"]["move_speed"]
                    if "home_speed" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["home_speed"] > 0:
                            self.galil_home_speed = c["motion"]["galil"]["home_speed"]
                    if "encdr_cnts_deg" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["encdr_cnts_deg"] > 0:
                            self.galil_encoder_counts_per_degree = c["motion"]["galil"]["encdr_cnts_deg"]
                    if "drive_cnts_deg" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["drive_cnts_deg"] > 0:
                            self.galil_drive_counts_per_degree = c["motion"]["galil"]["drive_cnts_deg"]
                    if "axis_names" in c["motion"]["galil"]:
                        if isinstance(c["motion"]["galil"]["axis_names"], dict):
                            self.galil_axis_names = c["motion"]["galil"]["axis_names"]
                if "limits" in c["motion"]:
                        if isinstance(c["motion"]["limits"], dict):
                            self.motion_limits = c["motion"]["limits"]
            if "positioner" in c:
                if "x_axis" in c["positioner"]:
                    if isinstance(c["positioner"]["x_axis"], str):
                        self.camera_x_axis = c["positioner"]["x_axis"]
                if "y_axis" in c["positioner"]:
                    if isinstance(c["positioner"]["y_axis"], str):
                        self.camera_y_axis = c["positioner"]["y_axis"]
            if "focuser" in c:
                if "focus_axis" in c["focuser"]:
                    if isinstance(c["focuser"]["focus_axis"], str):
                        self.focus_axis = c["focuser"]["focus_axis"]
                if "points_per_pass" in c["focuser"]:
                    if c["focuser"]["points_per_pass"] > 0:
                        self.focus_points_per_pass = c["focuser"]["points_per_pass"]
                if "frames_per_point" in c["focuser"]:
                    if c["focuser"]["frames_per_point"] > 0:
                        self.focus_frames_per_point = c["focuser"]["frames_per_point"]
                if "minimum_move" in c["focuser"]:
                    if c["focuser"]["minimum_move"] > 0:
                        self.focus_minimum_move = c["focuser"]["minimum_move"]
        except Exception as e:
            print(f"Error parsing config file {config_file}, using defaults\n{e}")
            self.default_config()

    def print_config(self):
        """Print all the config vars"""
        print(f"interval = {self.interval}")

        # camera
        print(f"camera_run_mode = {self.camera_run_mode}")
        print(f"camera_bits = {self.camera_bits}")
        print(f"camera_freq_mode = {self.camera_freq_mode}")
        print(f"camer_resolution = {self.camera_resolution}")
        print(f"camera_bin_mode = {self.camera_bin_mode}")
        print(f"camer_nBuffer = {self.camera_nBuffer}")
        print(f"camera_exposure_time = {self.camera_exposure_time}")
        print(f"camera_fps = {self.camera_fps}")
        print(f"camera_gain = {self.camera_gain}")
        print(f"pixel_size = {self.pixel_size}")

        # motion
        print(f"zaber_ports = {self.zaber_ports}")
        print(f"galil_address = {self.galil_address}")
        print(f"zaber_axis_names = {self.zaber_axis_names}")
        print(f"galil_axis_names = {self.galil_axis_names}")
        print(f"galil_acceleration = {self.galil_acceleration}")
        print(f"galil_deceleration = {self.galil_deceleration}")
        print(f"galil_move_speed = {self.galil_move_speed}")
        print(f"galil_home_speed = {self.galil_home_speed}")
        print(f"galil_encoder_counts_per_degree = {self.galil_encoder_counts_per_degree}")
        print(f"galil_drive_counts_per_degree = {self.galil_drive_counts_per_degree}")
        print(f"motion_limits = {self.motion_limits}")

        # positioner
        print(f"camera_x_axis = {self.camera_x_axis}")
        print(f"camera_y_axis = {self.camera_y_axis}")

        # focuser
        print(f"focus_axis = {self.focus_axis}")
        print(f"focus_points_per_pass = {self.focus_points_per_pass}")
        print(f"focus_frames_per_point = {self.focus_frames_per_point}")
        print(f"focus_minimum_move = {self.focus_minimum_move}")
