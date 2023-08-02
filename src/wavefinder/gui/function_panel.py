import asyncio
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ..functions.focus import Focuser
from ..functions.position import Positioner
from ..gui.utils import Cyclic
from .utils import make_task

if TYPE_CHECKING:
    from .app import App


class FunctionPanel(Cyclic, ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(self, parent: 'App', focuser: Focuser, positioner: Positioner):
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
        # TODO add output of best focus position
        ttk.Label(self, text="Auto Focus").grid(column=0, row=0, sticky=tk.E)
        self.focus_button = ttk.Button(self, text="Focus", command=self.focus)
        self.focus_button.grid(column=1, row=0, pady=(10, 0), padx=10)

    def make_positioner_slice(self):
        ttk.Label(self, text="Auto Position").grid(column=0, row=1, sticky=tk.E)
        self.center_button = ttk.Button(self, text="Center", command=self.center)
        self.center_button.grid(column=1, row=1, pady=(10, 0), padx=10)

    def focus(self):
        """Start focus routine"""
        make_task(self.focuser.focus(), self.tasks)
        self.focus_button.configure(state=tk.DISABLED)

    def center(self):
        """Center the image"""
        make_task(self.positioner.center(), self.tasks)

    async def update(self):
        """Update UI"""
        if len(self.tasks) == 0:
            self.focus_button.configure(state=tk.NORMAL)


    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()