import asyncio
import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.ascii import Axis
from zaber_motion.exceptions import MotionLibException

from devices.ZaberAdapter import AxisModel, ZaberAdapter

from .utils import valid_float


class MotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    # number of colors must match number of status codes
    COLORS = ["green", "yellow", "yellow", "red"]

    def __init__(self, parent, z_motion : ZaberAdapter|None):
        super().__init__(parent, text="Motion Control", labelanchor=tk.N)

        self.axes = z_motion.axes if z_motion else {}

        # UI variables
        self.pos : dict[str,tk.StringVar] = {}
        self.lights : dict[str,ttk.Label] = {}

        self.make_axes_position_slice()
        self.make_buttons()

        # initialize UI to current positions
        self.readback_axis_position()

    def make_axes_position_slice(self):
        row = 0
        for a in self.axes.values():
            # name
            ttk.Label(self, text=a.name).grid(column=0, row=row, sticky=tk.E)
            self.pos[a.name] = tk.StringVar(value=str(a.position))
            # position
            ttk.Entry(self, textvariable=self.pos[a.name], validate='focus',
                      validatecommand=(self.register(valid_float), '%P'),
                      invalidcommand=self.register(self.readback_axis_position),
                      width=6).grid(column=1, row=row, sticky=tk.W)
            # status light
            self.lights[a.name] = ttk.Label(self, width=1)
            self.lights[a.name].grid(column=2, row=row, sticky=tk.W)

    def make_buttons(self):
        ttk.Button(self, text="Home",
                   command=self.home_stages).grid(column=0, row=3,
                                                  pady=(10, 0), padx=10)
        ttk.Button(self, text="Move",
                   command=self.move_stages).grid(column=1, row=3, columnspan=2,
                                                  pady=(10, 0), padx=10)

    def move_stages(self):
        """Move Zaber stages"""
        for a in self.axes.values():
            try:
                a.axis.move_absolute(float(self.pos[a.name].get()),
                                     Units.LENGTH_MILLIMETRES,
                                     wait_until_idle=False)
                a.status = AxisModel.MOVING
            except MotionLibException:
                a.status = AxisModel.ERROR

    def home_stages(self):
        """Home all stages"""
        for a in self.axes.values():
            loop = asyncio.get_event_loop()
            is_homed = loop.run_until_complete(a.axis.is_homed_async())
            if not is_homed:
                try:
                    a.axis.home(wait_until_idle=False)
                    a.status = AxisModel.MOVING
                except MotionLibException:
                    a.status = AxisModel.ERROR
            # go to zero
            self.pos[a.name].set("0")
        self.move_stages()

    def readback_axis_position(self, axis_name : str|None = None):
        """Read axis positions and write back to UI
        
        axis_name: target axis name, None for all axis
        """
        for a in self.axes.values():
            # if axis is passed in, only target that one
            if axis_name and a.name != axis_name:
                continue
            p = a.axis.get_position(Units.LENGTH_MILLIMETRES)
            self.pos[a.name].set(str(p))

    async def update(self):
        """Cyclical task to update UI with axis info"""

        for a in self.axes.values():
            # check for warnings/errors
            w = await a.axis.warnings.get_flags_async()
            if len(w) > 0:
                a.status = AxisModel.ERROR

            # readback position, unless state is ready
            if a.status is not AxisModel.READY:
                self.readback_axis_position(a.name)

            # if status is moving, but axis is not busy,
            # set status to ready
            is_busy = await a.axis.is_busy_async()
            if a.status == AxisModel.MOVING and not is_busy:
                a.status = AxisModel.READY
            
            # set status light
            self.lights[a.name].configure(background=MotionPanel.COLORS[a.status])

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            await self.update()
            await asyncio.sleep(interval)