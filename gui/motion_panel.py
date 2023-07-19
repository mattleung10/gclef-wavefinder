import asyncio
import tkinter as tk
from tkinter import ttk

from devices.Axis import Axis

from .utils import valid_float


class MotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    # number of colors must match number of status codes
    COLORS = ["green", "yellow", "yellow", "red"]

    def __init__(self, parent, axes : dict[str, Axis]):
        super().__init__(parent, text="Zaber Slide Motion Control", labelanchor=tk.N)

        self.axes = axes

        # Task variables
        self.tasks : set[asyncio.Task] = set()

        # UI variables
        self.extra_init = True
        self.pos    : dict[str,tk.StringVar] = {}
        self.pos_in : dict[str, tk.StringVar] = {}
        self.lights : dict[str,ttk.Label] = {}
        self.jog_sel = tk.StringVar(self)

        r = self.make_header_slice()
        r = self.make_axes_position_slice(r)
        self.make_buttons(r)

    ### Panel Slices ###
    def make_header_slice(self) -> int:
        ttk.Label(self, text="Axis").grid(column=0, row=0, columnspan=3)
        ttk.Label(self, text="Jog").grid(column=3, row=0, columnspan=2)
        return 1

    def make_axes_position_slice(self, row : int) -> int:
        for a in self.axes.values():
            # name
            ttk.Label(self, text=a.name).grid(column=0, row=row, padx=10, sticky=tk.E)
            # position
            self.pos[a.name] = tk.StringVar(value=str(a.position))
            l = ttk.Label(self, textvariable=self.pos[a.name])
            l.grid(column=1, row=row, padx=10, sticky=tk.E)
            # position input
            self.pos_in[a.name] = tk.StringVar(value=str(0.0))
            e = ttk.Entry(self, textvariable=self.pos[a.name], validate='focus',
                          validatecommand=(self.register(valid_float), '%P'), width=6)
            e.grid(column=1, row=row, sticky=tk.W)
            # status light
            self.lights[a.name] = ttk.Label(self, width=1)
            self.lights[a.name].grid(column=2, row=row, sticky=tk.W)
            # jog selector
            r = ttk.Radiobutton(self, value=a.name, variable=self.jog_sel)
            r.grid(column=3, row=row, columnspan=2)

            row += 1
        return row

    def make_buttons(self, row : int):
        ttk.Button(self, text="Home",
                   command=self.home_stages).grid(column=0, row=row,
                                                  pady=(10, 0), padx=10)
        ttk.Button(self, text="Move",
                   command=self.move_stages).grid(column=1, row=row, columnspan=2,
                                                  pady=(10, 0), padx=10)
        self.jog_less = ttk.Button(self, text="◄", command=self.jog, width=3)
        self.jog_less.grid(column=3, row=row, pady=(10, 0), padx=2)
        self.jog_more = ttk.Button(self, text="►", command=self.jog, width=3)
        self.jog_more.grid(column=4, row=row, pady=(10, 0), padx=2)

    ### Functions ###
    def move_stages(self):
        """Move Zaber stages"""
        for a in self.axes.values():
            p = float(self.pos[a.name].get())
            t = asyncio.create_task(a.move_absolute(p))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)

    def home_stages(self):
        """Home all stages"""
        for a in self.axes.values():
            t = asyncio.create_task(a.home())
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)

    def jog(self):
        """Jog when button is pressed"""
        try:
            a = self.axes[self.jog_sel.get()]
        except KeyError:
            return

        if self.jog_less.instate(["active"]):
            t = asyncio.create_task(a.move_relative(-0.1))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)
        elif self.jog_more.instate(["active"]):
            t = asyncio.create_task(a.move_relative(+0.1))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)

    async def update(self):
        """Cyclical task to update UI with axis info"""

        # update device info and UI
        for a in self.axes.values():
            p = await a.get_position()
            s = await a.get_status()

            self.pos[a.name].set(str(round(p,3)))
            self.lights[a.name].configure(background=MotionPanel.COLORS[s])

            # on the first pass, set up some extra stuff
            if self.extra_init:
                self.pos_in[a.name].set(self.pos[a.name].get())
        self.extra_init = False

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
           await asyncio.gather(self.update(), asyncio.sleep(interval))

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()