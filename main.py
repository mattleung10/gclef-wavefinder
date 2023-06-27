import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk
from MightexBufCmos import Camera

class App(tk.Tk):
    """Main graphical application"""

    def __init__(self):
        super().__init__()
        self.title("Detector Stage Control")
        self.grid()

        self.set_defaults()
        self.make_frames()
        self.create_devices()
        self.start_tasks()
        self.hydrate()

    def set_defaults(self):
        """Set application defaults"""
        self.view_delay = 1000 // 60 # 60 Hz
        self.def_padding = "3 3 12 12"
        self.check_resolution = False
        self.camera_info1 = tk.StringVar(self, value="")
        self.camera_info2 = tk.StringVar(self, value="")
        self.img_props = tk.StringVar(self, "")

    def make_frames(self):
        """Make view frames"""

        self.make_camera_control_frame()

        # make image viewer frame
        viewer = ttk.Frame(self, padding=self.def_padding)
        viewer.grid(column=1, row=0)
        self.preview = ttk.Label(viewer)
        self.preview.grid(column=0, row=0, sticky=tk.W)
        ttk.Label(viewer, textvariable=self.img_props).grid(column=1,
                                                            row=0, sticky=tk.W)

        # make motion control frame
        motion = ttk.Frame(self, padding=self.def_padding)
        motion.grid(column=0, row=1)
        ttk.Label(motion, text="X").grid(column=0, row=0)
        ttk.Label(motion, text="Y").grid(column=0, row=1)
        ttk.Label(motion, text="Z").grid(column=0, row=2)

    def make_camera_control_frame(self):
        """Make camera control frame"""

        cam_ctrl = ttk.LabelFrame(self, text="Camera Control",
                                  labelanchor=tk.N, padding=self.def_padding)
        cam_ctrl.grid(column=0, row=0, sticky=tk.N)

        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_resolution1 = tk.StringVar(value="1280")
        self.camera_resolution2 = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        self.camera_exp_t = tk.StringVar(value="50.0")
        self.camera_fps = tk.StringVar(value="10.0")
        self.camera_gain = tk.StringVar(value="15")

        # camera info
        ttk.Label(cam_ctrl, text="Model").grid(column=0, row=0, sticky=tk.E, padx=10)
        ttk.Label(cam_ctrl, textvariable=self.camera_info1).grid(column=1, row=0,
                                                                 columnspan=2, sticky=tk.W)
        ttk.Label(cam_ctrl, text="S/N").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Label(cam_ctrl, textvariable=self.camera_info2).grid(column=1, row=1,
                                                                 columnspan=2, sticky=tk.W)

        # camera mode
        ttk.Label(cam_ctrl, text="Mode").grid(column=0, row=2, sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=2, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="8 bit", value=8,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl).grid(column=1, row=3, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="12 bit", value=12,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl, # TODO add 12-bit
                        state=tk.DISABLED).grid(column=2, row=3, sticky=tk.W)

        # resolution
        ttk.Label(cam_ctrl, text="Resolution").grid(column=0, row=4,
                                                    sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_resolution1,
                  validatecommand=(self.register(self.valid_resolution), '%P'),
                  validate='all').grid(column=1, row=4, sticky=tk.E)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_resolution2,
                  validatecommand=(self.register(self.valid_resolution), '%P'),
                  validate='all').grid(column=2, row=4, sticky=tk.W)

        # binning
        ttk.Label(cam_ctrl, text="Binning").grid(column=0, row=5,
                                                 sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="No Bin", value=Camera.NO_BIN,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=5,
                                                        columnspan=2,
                                                        sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:2", value=Camera.BIN1X2,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:3", value=Camera.BIN1X3,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=6, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4", value=Camera.BIN1X4,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=7, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4 skip", value=Camera.SKIP,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=7,
                                                        columnspan=2,
                                                        sticky=tk.W)

        # exposure time
        ttk.Label(cam_ctrl, text="Exp. Time (ms)").grid(column=0, row=8, sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_exp_t,
                  validatecommand=(self.register(self.valid_float), '%P'),
                  validate='all').grid(column=1, row=8, sticky=tk.W)

        # FPS
        ttk.Label(cam_ctrl, text="Frames per Sec").grid(column=0, row=9,
                                                        sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_fps,
                  validatecommand=(self.register(self.valid_float), '%P'),
                  validate='all').grid(column=1, row=9, sticky=tk.W)

        # gain
        ttk.Label(cam_ctrl, text="Gain [6-41]dB").grid(column=0, row=10,
                                                       sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_gain,
                  validatecommand=(self.register(self.valid_resolution), '%P'),
                  validate='all').grid(column=1, row=10, sticky=tk.W)

        # buttons
        ttk.Button(cam_ctrl, text="Take Image",
                   command=self.snap_img).grid(column=0, row=11, pady=(10, 0), padx=10)
        ttk.Button(cam_ctrl, text="Write to Camera",
                   command=self.set_cam_ctrl).grid(column=1, row=11, columnspan=2,
                                                   sticky=tk.E, pady=(10, 0), padx=10)


    def create_devices(self):
        """Create device handles"""
        try:
            self.camera = Camera()
        except ValueError as e:
            print(e)
            self.camera = None

    def start_tasks(self):
        """Start cyclic tasks."""
        self.preview.after(self.view_delay, self.update_preview)

    def hydrate(self):
        """Fill in UI elements"""
        if self.camera:
            info = self.camera.get_camera_info()
            self.camera_info1.set(info["ModuleNo"].strip('\0')) # type: ignore
            self.camera_info2.set(info["SerialNo"].strip('\0')) # type: ignore

    def update_preview(self):
        """Update preview image in viewer"""

        if self.camera:
            self.camera.acquire_frames()
            frame = self.camera.get_newest_frame()
            if frame:
                frame_img = Image.fromarray(frame.img)
                # frame_img = Image.fromarray(np.random.randint(255, size=(960, 1280), dtype=np.uint8)) # random noise
                disp_img = ImageTk.PhotoImage(frame_img.resize((frame_img.width // 4,
                                                                frame_img.height // 4)))
                self.preview.img = disp_img # protect from garbage collect
                self.preview.configure(image=disp_img)

                # update img_props
                prop_str = self.img_props.get()
                prop_str = ""
                for p in ["rows", "cols", "bin", "gGain", "expTime", "frameTime",
                          "timestamp", "triggered", "nTriggers", "freq"]:
                    prop_str += str(p) + ': ' + str(getattr(frame, p)) + '\n'
                self.img_props.set(prop_str)

                # update UI to proper values, matching newest frame
                if self.check_resolution:
                    resolution : tuple[int,int] = self.camera.query_buffer()["resolution"] # type: ignore
                    self.camera_resolution1.set(str(resolution[0]))
                    self.camera_resolution2.set(str(resolution[1]))
                    self.check_resolution = False

        self.preview.after(self.view_delay, self.update_preview)

    def set_cam_ctrl(self):
        """Set camera to new settings"""
        if self.camera:
            self.camera.set_mode(run_mode=self.camera_run_mode.get(),
                                 # TODO bits=self.camera_bits.get()
                                 write_now=True)
            resolution = tuple(np.clip((int(self.camera_resolution1.get()),
                          int(self.camera_resolution2.get())), 8, 65535))
            self.camera.set_resolution(resolution=resolution,
                                       bin_mode=self.camera_bin_mode.get(),
                                       write_now=True)
            self.camera.set_exposure_time(exposure_time=float(self.camera_exp_t.get()),
                                          write_now=True)
            self.camera.set_fps(fps=float(self.camera_fps.get()),
                                write_now=True)
            self.camera.set_gain(gain=int(self.camera_gain.get()),
                                 write_now=True)

            # throw out old frames
            self.camera.clear_buffer()

            # tell update_preview to also update the resolution
            self.check_resolution = True

            # read back validated settings from camera
            self.camera_exp_t.set(str(self.camera.exposure_time))
            self.camera_fps.set(str(self.camera.fps))
            self.camera_gain.set(str(self.camera.gain))

    def snap_img(self):
        """Snap and image"""
        if self.camera:
            self.camera.trigger()

    def valid_resolution(self, res_str : str):
        """Check if a resolution value is valid"""
        if str.isdigit(res_str):
            res = int(res_str)
            if int.bit_length(res) <= 16:
                return True
        return False

    def valid_float(self, f_str : str):
        """Check if a float value is valid"""
        try:
            float(f_str)
            return True
        except:
            return False


if __name__ == "__main__":
    app = App()
    app.mainloop()