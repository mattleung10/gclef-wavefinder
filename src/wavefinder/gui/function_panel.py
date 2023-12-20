import asyncio
import tkinter as tk
from tkinter import ttk

from ..functions.focus import Focuser
from ..functions.position import Positioner
from ..gui.utils import Cyclic
from .utils import make_task


class FunctionPanel(Cyclic, ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(self, parent: ttk.Frame, focuser: Focuser, positioner: Positioner):
        super().__init__(parent, text="Functions", labelanchor=tk.N)

        # Task variables
        self.tasks: set[asyncio.Task] = set()

        # focus variables
        self.focuser = focuser

        # position variables
        self.positioner = positioner

        self.make_focus_slice()
        self.make_positioner_slice()

        # TODO: function to read in table of positions;
        #       at each position:
        #           move to position
        #           center image
        #           focus
        #           take 3 images: [negative offset, on focus, positive offset]
        #           save images and a table of data

    def make_focus_slice(self):
        ttk.Label(self, text="Auto Focus").grid(column=0, row=0, sticky=tk.E)
        self.focus_button = ttk.Button(self, text="Focus", command=self.focus)
        self.focus_button.grid(column=1, row=0, pady=(10, 0), padx=10)
        self.focus_position = tk.StringVar(value="Not Yet Found")
        focus_readout = ttk.Label(self, textvariable=self.focus_position)
        focus_readout.grid(column=2, row=0)

    def make_positioner_slice(self):
        ttk.Label(self, text="Auto Position").grid(column=0, row=1, sticky=tk.E)
        self.center_button = ttk.Button(self, text="Center", command=self.center)
        self.center_button.grid(column=1, row=1, pady=(10, 0), padx=10)
        self.center_position = tk.StringVar(value="Not Yet Found")
        center_readout = ttk.Label(self, textvariable=self.center_position)
        center_readout.grid(column=2, row=1)

    def focus(self):
        """Start focus routine"""
        t, _ = make_task(self.focuser.focus(), self.tasks)
        t.add_done_callback(self.after_focus)
        self.focus_button.configure(state=tk.DISABLED)

    def after_focus(self, future: asyncio.Future):
        """Callback for after focus completes"""
        self.focus_position.set(str(round(future.result(), 3)))
        self.focus_button.configure(state=tk.NORMAL)

    def center(self):
        """Center the image"""
        t, _ = make_task(self.positioner.center(), self.tasks)
        t.add_done_callback(self.after_center)
        self.center_button.configure(state=tk.DISABLED)

    def after_center(self, future: asyncio.Future):
        """Callback for after center completes"""
        self.center_position.set(
            str(tuple(map(lambda v: round(v, 3), future.result())))
        )
        self.center_button.configure(state=tk.NORMAL)

    async def update(self):
        """Update UI"""
        pass

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()
