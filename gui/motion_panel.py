import asyncio
import tkinter as tk
from tkinter import ttk

from zaber_motion import Units
from zaber_motion.exceptions import MotionLibException

from devices.ZaberAdapter import ZaberAdapter, ZaberAxis

from .utils import valid_float


class MotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    # number of colors must match number of status codes
    COLORS = ["green", "yellow", "yellow", "red"]

    def __init__(self, parent, z_motion : ZaberAdapter|None):
        super().__init__(parent, text="Zaber Slide Motion Control", labelanchor=tk.N)

        self.axes = z_motion.axes if z_motion else {}

        # UI variables
        self.pos : dict[str,tk.StringVar] = {}
        self.lights : dict[str,ttk.Label] = {}
        self.jog_sel = tk.StringVar(self)
        self.readback = True # start with current positions

        r = self.make_header_slice()
        r = self.make_axes_position_slice(r)
        self.make_buttons(r)

    def set_readback_position(self):
        """Set the readback flag
        
        This will cause the update loop to readback all
        axes' positions and update the UI.
        """
        self.readback = True

    ### Panel Slices ###
    def make_header_slice(self) -> int:
        ttk.Label(self, text="Axis").grid(column=0, row=0, columnspan=3)
        ttk.Label(self, text="Jog").grid(column=3, row=0, columnspan=2)
        return 1

    def make_axes_position_slice(self, row : int) -> int:
        for a in self.axes.values():
            # name
            ttk.Label(self, text=a.name).grid(column=0, row=row, padx=10, sticky=tk.E)
            self.pos[a.name] = tk.StringVar(value=str(a.position))
            # position
            ttk.Entry(self, textvariable=self.pos[a.name], validate='focus',
                      validatecommand=(self.register(valid_float), '%P'),
                      invalidcommand=self.register(self.set_readback_position),
                      width=6).grid(column=1, row=row, sticky=tk.W)
            # status light
            self.lights[a.name] = ttk.Label(self, width=1)
            self.lights[a.name].grid(column=2, row=row, sticky=tk.W)
            # jog selector
            ttk.Radiobutton(self, value=a.name,
                            variable=self.jog_sel).grid(column=3, row=row, columnspan=2)
            row += 1
        return row

    def make_buttons(self, row : int):
        ttk.Button(self, text="Home",
                   command=self.home_stages).grid(column=0, row=row,
                                                  pady=(10, 0), padx=10)
        ttk.Button(self, text="Move",
                   command=self.move_stages).grid(column=1, row=row, columnspan=2,
                                                  pady=(10, 0), padx=10)
        self.jog_less = ttk.Button(self, text="◄", width=3)
        self.jog_less.grid(column=3, row=row, pady=(10, 0), padx=2)
        self.jog_more = ttk.Button(self, text="►", width=3)
        self.jog_more.grid(column=4, row=row, pady=(10, 0), padx=2)

    ### Functions ###
    def move_stages(self):
        """Move Zaber stages"""
        for a in self.axes.values():
            try:
                a.axis.move_absolute(float(self.pos[a.name].get()),
                                     Units.LENGTH_MILLIMETRES,
                                     wait_until_idle=False)
                a.status = ZaberAxis.MOVING
            except MotionLibException:
                a.status = ZaberAxis.ERROR

    async def home_one_axis(self, a : ZaberAxis):
        """Home one axis, async"""
        is_homed = await a.axis.is_homed_async()
        if not is_homed:
            try:
                a.axis.home(wait_until_idle=False)
                a.status = ZaberAxis.MOVING
            except MotionLibException:
                a.status = ZaberAxis.ERROR
    
    def home_stages(self):
        """Home all stages"""
        for a in self.axes.values():
            asyncio.create_task(self.home_one_axis(a))

    def jog(self):
        """Jog while button is pressed"""
        try:
            a = self.axes[self.jog_sel.get()]
        except KeyError:
            return

        try:
            if self.jog_less.instate(["pressed"]):
                a.axis.move_relative(-0.1, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
                a.status = ZaberAxis.MOVING
            elif self.jog_more.instate(["pressed"]):
                a.axis.move_relative(+0.1, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
                a.status = ZaberAxis.MOVING
        except MotionLibException:
            pass

    async def update(self):
        """Cyclical task to update UI with axis info"""

        self.jog()

        # update UI
        for a in self.axes.values():
            # readback position if set or axis is not ready
            # We don't want to readback in the READY state because it would
            # override user input.
            if self.readback or a.status is not ZaberAxis.READY:
                p = await a.axis.get_position_async(Units.LENGTH_MILLIMETRES)
                self.pos[a.name].set(str(round(p,3)))

            # set status to ready and turn off readback if axis is not busy
            if not await a.axis.is_busy_async():
                a.status = ZaberAxis.READY
                self.readback = False

            # check for warnings/errors; do last to override READY flag
            w = await a.axis.warnings.get_flags_async()
            if len(w) > 0:
                a.status = ZaberAxis.ERROR
            
            # set status light
            self.lights[a.name].configure(background=MotionPanel.COLORS[a.status])

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            await self.update()
            await asyncio.sleep(interval)