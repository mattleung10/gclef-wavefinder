import asyncio
import tkinter as tk
from tkinter import ttk

from ..devices.DkMonochromator import DkMonochromator

from ..gui.utils import Cyclic
from ..gui.config import Configuration

class MonochromPanel(Cyclic, ttk.LabelFrame):
    """Monochromater Control Panel"""

    def __init__(
        self,
        parent: ttk.Frame,
        config: Configuration,
        dk: DkMonochromator
    ):
        super().__init__(parent, text="Monochromator", labelanchor=tk.N)
        self.config = config
        self.dk = dk

        self.tasks: set[asyncio.Task] = set()





    async def update(self):
        """Update UI"""
        pass

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()


