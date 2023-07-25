import asyncio
import tkinter as tk
from tkinter import ttk

from devices.Axis import Axis

from .utils import valid_float


class MotionPanel(ttk.LabelFrame):
    """Dector 3D Motion UI Panel"""

    # number of colors must match number of status codes
    COLORS = ["green", "yellow", "yellow", "red"]

    def __init__(self, parent, axes: dict[str, Axis]):
        super().__init__(parent, text="Motion Control", labelanchor=tk.N)

        self.axes = axes

        # Task variables
        self.tasks: set[asyncio.Task] = set()
        self.extra_init = True

        # UI variables
        self.pos:    dict[str, tk.StringVar] = {}
        self.pos_in: dict[str, tk.StringVar] = {}
        self.lights: dict[str, ttk.Label] = {}
        self.home_sel: dict[str, tk.IntVar] = {}
        self.jog_sel = tk.StringVar(self)

        r = self.make_header_slice()
        r = self.make_axes_position_slice(r)
        self.make_buttons(r)

    ### Panel Slices ###
    def make_header_slice(self) -> int:
        ttk.Label(self, text="Axis").grid(column=0, row=0, pady=10)
        ttk.Label(self, text="Position").grid(column=1, row=0)
        ttk.Label(self, text="Input").grid(column=2, row=0)
        ttk.Label(self, text="Jog").grid(column=4, row=0)
        ttk.Label(self, text="Home").grid(column=5, row=0)
        return 1

    def make_axes_position_slice(self, row: int) -> int:
        for a in self.axes.values():
            # name
            ttk.Label(self, text=a.name).grid(column=0, row=row, padx=10, sticky=tk.E)
            # position
            self.pos[a.name] = tk.StringVar(value=str(a.position))
            l = ttk.Label(self, textvariable=self.pos[a.name])
            l.grid(column=1, row=row, padx=10, sticky=tk.E)
            # position input
            self.pos_in[a.name] = tk.StringVar(value=str(0.0))
            e = ttk.Entry(self, textvariable=self.pos_in[a.name], validate='focus',
                          validatecommand=(self.register(valid_float), '%P'), width=6)
            e.grid(column=2, row=row, sticky=tk.W)
            # status light
            self.lights[a.name] = ttk.Label(self, width=1)
            self.lights[a.name].grid(column=3, row=row, padx=10)
            # jog selector
            r = ttk.Radiobutton(self, value=a.name, variable=self.jog_sel)
            r.grid(column=4, row=row)
            # home selector
            self.home_sel[a.name] = tk.IntVar(value=0)
            c = ttk.Checkbutton(self, variable=self.home_sel[a.name])
            c.grid(column=5,row=row)

            row += 1
        return row

    def make_buttons(self, row: int):
        s = ttk.Button(self, text="Stop", command=self.stop_stages)
        s.grid(column=0, row=row, pady=(10, 0), padx=10)

        m = ttk.Button(self, text="Move", command=self.move_stages)
        m.grid(column=1, row=row, columnspan=2, pady=(10, 0), padx=10)

        self.jog_less = ttk.Button(self, text="◄", command=self.jog, width=3)
        self.jog_less.grid(column=4, row=row, pady=(10, 0), padx=2)
        self.jog_more = ttk.Button(self, text="►", command=self.jog, width=3)
        self.jog_more.grid(column=5, row=row, pady=(10, 0), padx=2)
        # 2nd row
        z = ttk.Button(self, text="Zero Input", command=self.zero_input)
        z.grid(column=0, row=row+1, pady=(10, 0), padx=10)
        cp = ttk.Button(self, text="Copy Position", command=self.copy_position)
        cp.grid(column=1, row=row+1, columnspan=2, pady=(10, 0), padx=10)
        h = ttk.Button(self, text="Home", command=self.home_stages)
        h.grid(column=4, row=row+1, columnspan=2, pady=(10, 0), padx=10)

    ### Functions ###
    def stop_stages(self):
        "Stop all stages"
        for a in self.axes.values():
            t= asyncio.create_task(a.stop())
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)

    def move_stages(self):
        """Move all stages"""
        for a in self.axes.values():
            p = float(self.pos_in[a.name].get())
            t = asyncio.create_task(a.move_absolute(p))
            t.add_done_callback(self.tasks.discard)
            self.tasks.add(t)

    def home_stages(self):
        """Home all stages"""
        for name, axis in self.axes.items():
            if self.home_sel[name].get() == 1:
                t = asyncio.create_task(axis.home())
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

    def copy_position(self):
        """Copy position to input"""
        for a in self.axes.keys():
            self.pos_in[a].set(self.pos[a].get())

    def zero_input(self):
        """Zero position input"""
        for a in self.axes.keys():
            self.pos_in[a].set("0")

    async def update(self):
        """Cyclical task to update UI with axis info"""
        for a in self.axes.values():
            # on the first pass, set up some extra stuff
            if self.extra_init:
                await a.update_position()
                await a.update_status()
                self.pos_in[a.name].set(str(round(a.position, 3)))
            self.pos[a.name].set(str(round(a.position, 3)))
            self.lights[a.name].configure(background=MotionPanel.COLORS[a.status])
        self.extra_init = False

    async def update_loop(self, interval: float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
           await asyncio.gather(self.update(), asyncio.sleep(interval))

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()