import tkinter as tk
from tkinter import ttk

from focus import Focuser

class FunctionPanel(ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(self, parent, focuser : Focuser,
                 view_delay : int):
        super().__init__(parent, text="Functions", labelanchor=tk.N)

        # UI variables
        self.view_delay = view_delay

        self.make_focus_slice()

    def make_focus_slice(self):
        ttk.Label(self, text="Focus").grid(column=0, row=0)
        ttk.Button(self, text="Focus",
                   command=self.focus).grid(column=1, row=0,
                                            pady=(10, 0), padx=10)


    def focus(self):
        pass

    def update(self):
        pass