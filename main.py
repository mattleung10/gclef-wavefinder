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

    def make_frames(self):
        """Make view frames"""

        # make camera control frame
        cam_ctrl = ttk.Frame(self, padding=self.def_padding)
        cam_ctrl.grid(column=0, row=0)
        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        ttk.Label(cam_ctrl, text="Camera Settings").grid(columnspan=3, row=0)
        ttk.Label(cam_ctrl, text="Mode: ").grid(column=0, row=1)
        ttk.Radiobutton(cam_ctrl, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode).grid(column=1, row=1)
        ttk.Radiobutton(cam_ctrl, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode).grid(column=2, row=1)

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
        self.camera = Camera()
        self.camera.print_introduction()
        
    def start_tasks(self):
        """Start cyclic tasks."""
        self.preview.after(self.view_delay, self.update_preview)
        
    def update_preview(self):
        """Update preview image in viewer"""

        self.camera.acquire_frames()
        frame = self.camera.get_newest_frame()
        frame_img = Image.fromarray(frame.img)
        # frame_img = Image.fromarray(np.random.randint(255, size=(960, 1280), dtype=np.uint8)) # random noise
        disp_img = ImageTk.PhotoImage(frame_img.resize((frame_img.width // 4,
                                                        frame_img.height // 4)))

        self.preview.img = disp_img # protect from garbage collect
        self.preview.configure(image=disp_img)
        self.preview.after(self.view_delay, self.update_preview)

    def set_cam_ctrl(self):
        """Set camera to new settings"""
        self.camera.run_mode = self.camera_run_mode.get()
        self.camera.write_configuration()


if __name__ == "__main__":
    app = App()
    app.mainloop()