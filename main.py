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

    def set_defaults(self):
        """Set application defaults"""
        self.view_delay = 1000 // 60 # 60 Hz
        self.def_padding = "3 3 12 12"
        self.check_resolution = False

    def make_frames(self):
        """Make view frames"""

        # make camera control frame
        cam_ctrl = ttk.Frame(self, padding=self.def_padding)
        cam_ctrl.grid(column=0, row=0)
        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_resolution1 = tk.StringVar(value="1280")
        self.camera_resolution2 = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        ttk.Label(cam_ctrl, text="Camera Settings").grid(columnspan=4, row=0)
        ttk.Label(cam_ctrl, text="Mode").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=1, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=1, sticky=tk.W)
        ttk.Button(cam_ctrl, text="Snap", command=self.snap_img,
                   width=4).grid(column=3, row=1, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="8 bit", value=8,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="12 bit", value=12,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl, # TODO add 12-bit
                        state=tk.DISABLED).grid(column=2, row=2, sticky=tk.W)
        ttk.Label(cam_ctrl, text="Resolution").grid(column=0, row=3,
                                                    sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_resolution1,
                  validatecommand=(self.register(self.valid_resolution), '%P'),
                  validate='all').grid(column=1, row=3, sticky=tk.E)
        ttk.Entry(cam_ctrl, width=5,textvariable=self.camera_resolution2,
                  validatecommand=(self.register(self.valid_resolution), '%P'),
                  validate='all').grid(column=2, row=3, sticky=tk.W)
        ttk.Button(cam_ctrl, text="Set", command=self.set_cam_ctrl,
                   width=4).grid(column=3, row=3, sticky=tk.W)
        ttk.Label(cam_ctrl, text="Binning").grid(column=0, row=4,
                                                 sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="No Bin", value=Camera.NO_BIN,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=4, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:2", value=Camera.BIN1X2,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=5, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:3", value=Camera.BIN1X3,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=5, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4", value=Camera.BIN1X4,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4 skip", value=Camera.SKIP,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=6, sticky=tk.W)

        # make image viewer frame
        viewer = ttk.Frame(self, padding=self.def_padding)
        viewer.grid(column=1, row=0)
        self.preview = ttk.Label(viewer)
        self.preview.grid(column=0, row=0)
        ttk.Label(viewer, text="properties").grid(column=0, row=1)

        # make motion control frame
        motion = ttk.Frame(self, padding=self.def_padding)
        motion.grid(column=0, row=1)
        ttk.Label(motion, text="X").grid(column=0, row=0)
        ttk.Label(motion, text="Y").grid(column=0, row=1)
        ttk.Label(motion, text="Z").grid(column=0, row=2)

    def create_devices(self):
        """Create device handles"""
        try:
            self.camera = Camera()
            self.camera.print_introduction()
        except ValueError as e:
            print(e)
            self.camera = None

    def start_tasks(self):
        """Start cyclic tasks."""
        self.preview.after(self.view_delay, self.update_preview)

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
            # throw out old frames
            self.camera.clear_buffer()
            # tell update_preview to also update the resolution
            self.check_resolution = True

    def snap_img(self):
        """Snap and image"""
        if self.camera and self.camera_run_mode.get() == Camera.TRIGGER:
            self.camera.trigger()

    def valid_resolution(self, res_str : str):
        """Check if a resolution value is valid"""
        if str.isdigit(res_str):
            res = int(res_str)
            if int.bit_length(res) <= 16:
                return True
        return False


if __name__ == "__main__":
    app = App()
    app.mainloop()