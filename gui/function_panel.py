import asyncio
import tkinter as tk
from tkinter import ttk

from functions.focus import Focuser
from functions.position import Positioner


class FunctionPanel(ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(self, parent, focuser : Focuser, positioner : Positioner):
        super().__init__(parent, text="Functions", labelanchor=tk.N)

        # focus variables
        self.focuser = focuser
        self.focus_task = None

        # position variables
        self.positioner = positioner
        self.position_task = None

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

    def make_positioner_slice(self):
        ttk.Label(self, text="Auto Position").grid(column=0, row=1, sticky=tk.E)
        self.center_button = ttk.Button(self, text="Center", command=self.center)
        self.center_button.grid(column=1, row=1, pady=(10, 0), padx=10)

    def focus(self):
        """Start focus routine"""
        self.focus_task = asyncio.create_task(asyncio.to_thread(self.focuser.focus))
        self.focus_button.configure(state=tk.DISABLED)

    def center(self):
        """Center the image"""
        self.position_task = asyncio.create_task(asyncio.to_thread(self.positioner.center))

    def update(self, interval : float = 1):
        """Update UI
   
        interval: time in seconds between updates
        """
        if self.focus_task:
            if self.focus_task.done() and tk.DISABLED in self.focus_button.state():
                self.focus_button.configure(state=tk.NORMAL)

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            self.update()
            await asyncio.sleep(interval)