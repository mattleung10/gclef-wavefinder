import tomllib

from PIL import Image

from ..devices.MightexBufCmos import Camera, Frame


class Configuration:
    """Application configuration object"""

    def __init__(self, config_filename: str) -> None:
        """Application configuration object

        Args:
            config_filename: name of config file
        """
        self.set_defaults()
        self.read_config_file(config_filename)

    def set_defaults(self):
        "Set configuration to default."
        # task defaults
        self.interval = 1 / 60  # seconds

        # camera defaults
        self.camera_run_mode = Camera.NORMAL
        self.camera_bits = 8
        self.camera_freq_mode = 0
        self.camera_resolution = (1280, 960)
        self.camera_bin_mode = Camera.NO_BIN
        self.camera_nBuffer = 24
        self.camera_exposure_time = 5.0
        self.camera_fps = 5.0
        self.camera_gain = 15
        self.camera_pixel_size = (3.75, 3.75)
        self.camera_frame: Frame | None = None

        # image processing defaults and state
        self.full_img = Image.new(mode="L", size=self.camera_resolution)
        self.image_frozen = False
        self.image_full_threshold = 50.0
        self.image_roi_threshold = 50.0
        self.roi_size = (50, 50)
        self.image_use_roi_stats = False
        self.img_stats = {
            "size_x": 0,
            "size_y": 0,
            "cen_x": 0.0,
            "cen_y": 0.0,
            "var_x": 0.0,
            "var_y": 0.0,
            "covar": 0.0,
            "max": 0,
            "n_sat": 0,
        }

        # motion defaults
        self.zaber_ports = [
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "COM10",
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
            "/dev/ttyUSB2",
            "/dev/ttyUSB3",
        ]
        self.galil_address = "192.168.1.19"
        self.zaber_axis_names = {
            "detector x": {"sn": 33938, "keyword": "detxpos"},
            "detector y": {"sn": 33937, "keyword": "detypos"},
            "detector z": {"sn": 33939, "keyword": "detzpos"},
            "cfm2 x": {"sn": 110098, "keyword": "cfm2xpos"},
            "cfm2 y": {"sn": 113059, "keyword": "cfm2ypos"},
        }
        self.galil_axis_names = {
            "cfm1 azimuth": {"ch": "A", "keyword": "cfm1az"},
            "cfm1 elevation": {"ch": "B", "keyword": "cfm1el"},
            "cfm2 azimuth": {"ch": "C", "keyword": "cfm2az"},
            "cfm2 elevation": {"ch": "D", "keyword": "cfm2el"},
        }
        self.galil_acceleration = 2000000
        self.galil_deceleration = 2000000
        self.galil_move_speed = 100000
        self.galil_home_speed = 5000
        self.galil_encoder_counts_per_degree = 800
        self.galil_drive_counts_per_degree = 10000
        self.motion_limits = {
            "detector z": {"min": 0.0, "max": 15.0},
            "cfm1 azimuth": {"min": -30.0, "max": 30.0},
            "cfm1 elevation": {"min": -30.0, "max": 30.0},
            "cfm2 azimuth": {"min": -30.0, "max": 30.0},
            "cfm2 elevation": {"min": -30.0, "max": 30.0},
        }

        # positioner defaults
        self.camera_x_axis = "detector x"
        self.camera_y_axis = "detector y"

        # focuser defaults
        self.focus_axis = "detector z"
        self.focus_points_per_pass = 10
        self.focus_frames_per_point = 3
        self.focus_minimum_move = 0.001

        # writer defaults
        self.writer_obstypes = [
            "STANDARD",
            "BIAS",
            "DARK",
            "FLAT",
        ]

    def read_config_file(self, config_filename: str) -> None:
        """Read configuration file, validate input, overwrite defaults.

        Args:
            config_filename: name of config file
        """
        try:
            with open(config_filename, "rb") as f:
                c = tomllib.load(f)
        except FileNotFoundError as e:
            print(f"Can't find config file {e.filename}, using defaults")
            return
        except tomllib.TOMLDecodeError as e:
            print(f"Error loading config file {config_filename}, using defaults\n{e}")
            return

        try:
            if "app" in c:
                if "update_rate" in c["app"]:
                    self.interval = float(c["app"]["update_rate"])
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
                        self.camera_freq_mode = int(c["camera"]["freq_mode"])
                if "resolution" in c["camera"]:
                    if "rows" in c["camera"]["resolution"]:
                        rows = c["camera"]["resolution"]["rows"]
                        if "columns" in c["camera"]["resolution"]:
                            cols = c["camera"]["resolution"]["columns"]
                            if rows in range(1280) and cols in range(960):
                                self.camera_resolution = (int(rows), int(cols))
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
                        self.camera_nBuffer = int(c["camera"]["nBuffer"])
                if "exposure" in c["camera"]:
                    if isinstance(c["camera"]["exposure"], float):
                        self.camera_exposure_time = float(c["camera"]["exposure"])
                if "fps" in c["camera"]:
                    if isinstance(c["camera"]["fps"], float):
                        self.camera_fps = float(c["camera"]["fps"])
                if "gain" in c["camera"]:
                    if c["camera"]["gain"] in range(6, 42):
                        self.camera_gain = int(c["camera"]["gain"])
            if "image" in c:
                if "full_threshold" in c["image"]:
                    if isinstance(c["image"]["full_threshold"], float):
                        self.image_full_threshold = float(c["image"]["full_threshold"])
                if "roi_threshold" in c["image"]:
                    if isinstance(c["image"]["roi_threshold"], float):
                        self.image_roi_threshold = float(c["image"]["roi_threshold"])
                if "roi_size" in c["image"]:
                    if "x" in c["image"]["roi_size"]:
                        x = c["image"]["roi_size"]["x"]
                        if "y" in c["image"]["roi_size"]:
                            y = c["image"]["roi_size"]["y"]
                            if x in range(1280) and y in range(960):
                                self.roi_size = (int(x), int(y))
                if "use_roi_stats" in c["image"]:
                    if isinstance(c["image"]["use_roi_stats"], bool):
                        self.image_use_roi_stats = bool(c["image"]["use_roi_stats"])
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
                            self.galil_acceleration = c["motion"]["galil"][
                                "acceleration"
                            ]
                    if "deceleration" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["deceleration"] > 0:
                            self.galil_deceleration = c["motion"]["galil"][
                                "deceleration"
                            ]
                    if "move_speed" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["move_speed"] > 0:
                            self.galil_move_speed = c["motion"]["galil"]["move_speed"]
                    if "home_speed" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["home_speed"] > 0:
                            self.galil_home_speed = c["motion"]["galil"]["home_speed"]
                    if "encdr_cnts_deg" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["encdr_cnts_deg"] > 0:
                            self.galil_encoder_counts_per_degree = c["motion"]["galil"][
                                "encdr_cnts_deg"
                            ]
                    if "drive_cnts_deg" in c["motion"]["galil"]:
                        if c["motion"]["galil"]["drive_cnts_deg"] > 0:
                            self.galil_drive_counts_per_degree = c["motion"]["galil"][
                                "drive_cnts_deg"
                            ]
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
            print(f"Error parsing config file {config_filename}, using defaults\n{e}")
            self.set_defaults()

    def __str__(self) -> str:
        return str(self.__dict__)
