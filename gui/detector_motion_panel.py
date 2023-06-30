import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.ascii import Axis

from .utils import valid_float, valid_int


class DetectorMotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    def __init__(self, parent, ax : Axis | None,
                               ay : Axis | None,
                               az : Axis | None):
        super().__init__(parent, text="Detector 3D Stage", labelanchor=tk.N)

        self.ax = ax
        self.ay = ay
        self.az = az

        self.pos_x = tk.StringVar(value="0")
        self.pos_y = tk.StringVar(value="0")
        self.pos_z = tk.StringVar(value="0")

        ttk.Label(self, text="X").grid(column=0, row=0)
        ttk.Entry(self, width=5, textvariable=self.pos_x,
            validatecommand=(self.register(valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=0, sticky=tk.E)
        ttk.Label(self, text="Y").grid(column=0, row=1)
        ttk.Entry(self, width=5, textvariable=self.pos_y,
            validatecommand=(self.register(valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=1, sticky=tk.E)
        ttk.Label(self, text="Z").grid(column=0, row=2)
        ttk.Entry(self, width=5, textvariable=self.pos_z,
            validatecommand=(self.register(valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=2, sticky=tk.E)
        ttk.Button(self, text="Go",
                   command=self.move_stages).grid(column=0, row=3)
        
    def move_stages(self):
        """Move Zaber stages"""
        if self.ax:
            self.ax.move_absolute(float(self.pos_x.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        if self.ay:
            self.ay.move_absolute(float(self.pos_y.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        if self.az:
            self.az.move_absolute(float(self.pos_z.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
