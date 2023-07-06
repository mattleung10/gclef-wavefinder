import asyncio
import tkinter as tk
from tkinter import ttk

from functions.focus import Focuser

class FunctionPanel(ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(self, parent, focuser : Focuser):
        super().__init__(parent, text="Functions", labelanchor=tk.N)

        self.focuser = focuser
        self.make_focus_slice()

    def make_focus_slice(self):
        ttk.Label(self, text="Focus").grid(column=0, row=0)
        ttk.Button(self, text="Focus",
                   command=self.focus).grid(column=1, row=0,
                                            pady=(10, 0), padx=10)

    def focus(self):
        """Start focus routine"""
        asyncio.create_task(asyncio.to_thread(self.focuser.focus))

    def update(self, interval : float = 1):
        """Update UI
   
        interval: time in seconds between updates
        """
        pass

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            self.update()
            await asyncio.sleep(interval)