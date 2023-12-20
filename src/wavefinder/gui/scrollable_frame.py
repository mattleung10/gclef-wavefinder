import tkinter as tk
from tkinter import ttk


class ScrollableContainer(ttk.Frame):
    """A Scrollable Frame

    Puts a frame inside a canvas with scrollbars.
    Add your elements to the frame.
    """

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        canvas = tk.Canvas(self)
        scrollbar_v = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=canvas.xview)
        sizegrip = ttk.Sizegrip(self)
        self.frame = ttk.Frame(canvas)

        # place frame inside canvas
        canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # make canvas scale with frame size
        self.frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        # make scrollbars match scroll position
        canvas.configure(yscrollcommand=scrollbar_v.set)
        canvas.configure(xscrollcommand=scrollbar_h.set)

        # place elements, canvas takes all extra space
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        scrollbar_v.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_h.grid(row=1, column=0, sticky=tk.EW)
        sizegrip.grid(row=1, column=1)
        canvas.grid(row=0, column=0, sticky=tk.NSEW)
