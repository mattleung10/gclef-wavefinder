import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.ascii import Axis

from .utils import valid_float


class MotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    def __init__(self, parent, ax : Axis | None,
                               ay : Axis | None,
                               az : Axis | None, view_delay : int):
        super().__init__(parent, text="Detector 3D Stage", labelanchor=tk.N)

        # UI variables
        self.view_delay = view_delay
        self.pos =      {"x": tk.StringVar(value="0"),
                         "y": tk.StringVar(value="0"),
                         "z": tk.StringVar(value="0")}
        self.status =   {"x": 2,
                         "y": 2,
                         "z": 2}
        self.lights =   {"x": ttk.Label(self, width=1),
                         "y": ttk.Label(self, width=1),
                         "z": ttk.Label(self, width=1)}
        self.colors = ["green", "yellow", "red"]

        # Motion variables
        self.axes = {"x": ax,
                     "y": ay,
                     "z": az}

        self.make_axes_position_slice()
        self.make_buttons()

    def make_axes_position_slice(self):
        ttk.Label(self, text="x").grid(column=0, row=0)
        ttk.Entry(self, width=5, textvariable=self.pos["x"],
            validatecommand=(self.register(valid_float), '%P'),
            invalidcommand=self.register(self.readback_axis_position),
            validate='focus').grid(column=1, row=0, sticky=tk.W)
        self.lights["x"].grid(column=2, row=0, sticky=tk.W)

        ttk.Label(self, text="y").grid(column=0, row=1)
        ttk.Entry(self, width=5, textvariable=self.pos["y"],
            validatecommand=(self.register(valid_float), '%P'),
            invalidcommand=self.register(self.readback_axis_position),
            validate='focus').grid(column=1, row=1, sticky=tk.W)
        self.lights["y"].grid(column=2, row=1, sticky=tk.W)

        ttk.Label(self, text="z").grid(column=0, row=2)
        ttk.Entry(self, width=5, textvariable=self.pos["z"],
            validatecommand=(self.register(valid_float), '%P'),
            invalidcommand=self.register(self.readback_axis_position),
            validate='focus').grid(column=1, row=2, sticky=tk.W)
        self.lights["z"].grid(column=2, row=2, sticky=tk.W)

    def make_buttons(self):
        ttk.Button(self, text="Home",
                   command=self.home_stages).grid(column=0, row=3,
                                                  pady=(10, 0), padx=10)
        ttk.Button(self, text="Move",
                   command=self.move_stages).grid(column=1, row=3, columnspan=2,
                                                  pady=(10, 0), padx=10)

    def move_stages(self):
        """Move Zaber stages"""
        for k in self.axes.keys():
            a = self.axes[k]
            if a:
                a.move_absolute(float(self.pos[k].get()), Units.LENGTH_MILLIMETRES,
                                wait_until_idle=False)

    def home_stages(self):
        """Home all stages"""
        for k in self.axes.keys():
            a = self.axes[k]
            if a and not a.is_homed():
                a.home(wait_until_idle=False)

    def readback_axis_position(self, axis : str|None = None):
        """Read axis positions and write back to UI
        
        axis: target axis name, None for all axis
        """
        for k in self.axes.keys():
            # if axis is passed in, only target that one
            if axis and k != axis:
                continue
            a = self.axes[k]
            if a:
                self.pos[k].set(str(a.get_position(Units.LENGTH_MILLIMETRES)))

    def update(self):
        """Cyclical task to update UI with axis status"""

        # update axes status and position
        for k in self.axes.keys():
            a = self.axes[k]
            if a:
                if a.is_busy():
                    self.readback_axis_position(k)
                    self.status[k] = 1 # busy
                else:
                    self.status[k] = 0 # ready
                # TODO: check for warnings, clear them, etc.
                if len(a.warnings.get_flags()) > 0:
                    self.status[k] = 2 # error/warning/alert

            self.lights[k].configure(background=self.colors[self.status[k]])

        # TODO: once all axes are finish moving, update positions one last time

        self.after(self.view_delay, self.update)
