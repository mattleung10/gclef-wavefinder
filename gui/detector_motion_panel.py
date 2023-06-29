import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.ascii import Axis

from .utils import valid_float, valid_int


class DetectorMotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    def __init__(self, parent, det_ax : Axis | None,
                               det_ay : Axis | None,
                               det_az : Axis | None):
        super().__init__(parent, text="Detector 3D Stage", labelanchor=tk.N)

        self.det_ax = det_ax
        self.det_ay = det_ay
        self.det_az = det_az

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
        if self.det_ax:
            self.det_ax.move_absolute(float(self.pos_x.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        if self.det_ay:
            self.det_ay.move_absolute(float(self.pos_y.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        if self.det_az:
            self.det_az.move_absolute(float(self.pos_z.get()), Units.LENGTH_MILLIMETRES, wait_until_idle=False)
