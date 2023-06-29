import tkinter as tk
from tkinter import ttk

class App(tk.Tk):
    """Main graphical application"""

    def __init__(self):
        super().__init__()
        self.title("Detector Stage Control")
        self.grid()

        self.make_frames()

    def make_frames(self):
        """Make view frames"""

        self.make_camera_control_frame()
        self.make_image_viewer_frame()

        # make motion control frame
        motion = ttk.Frame(self, padding=self.def_padding)
        motion.grid(column=0, row=1)
        
        self.pos_x = tk.StringVar(value="0")
        self.pos_y = tk.StringVar(value="0")
        self.pos_z = tk.StringVar(value="0")

        ttk.Label(motion, text="X").grid(column=0, row=0)
        ttk.Entry(motion, width=5, textvariable=self.pos_x,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=0, sticky=tk.E)
        ttk.Label(motion, text="Y").grid(column=0, row=1)
        ttk.Entry(motion, width=5, textvariable=self.pos_y,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=1, sticky=tk.E)
        ttk.Label(motion, text="Z").grid(column=0, row=2)
        ttk.Entry(motion, width=5, textvariable=self.pos_z,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=2, sticky=tk.E)
        ttk.Button(motion, text="Go",
                   command=self.move_stages).grid(column=0, row=3)