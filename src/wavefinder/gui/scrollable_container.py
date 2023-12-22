import tkinter as tk
from tkinter import ttk


class ScrollableWindow(tk.Tk):
    """A Scrollable Tk App window

    Puts a frame inside a canvas with scrollbars.
    Add your elements to the frame.
    """

    def __init__(self):
        super().__init__()

        self.canvas = tk.Canvas(self)
        self.scrollbar_v = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar_h = ttk.Scrollbar(
            self, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        self.sizegrip = ttk.Sizegrip(self)
        self.frame = ttk.Frame(self.canvas)

        # place frame inside canvas
        self.window = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # make canvas scale with frame size and visa versa
        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)
        # make scrollbars match scroll position
        self.canvas.configure(yscrollcommand=self.scrollbar_v.set)
        self.canvas.configure(xscrollcommand=self.scrollbar_h.set)

        # place elements, canvas takes all extra space
        # NOTE: set border to -9 px because it's 10px even with zero setting,
        #       so this yields a 1px border all around
        self.configure(bd=-9)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.scrollbar_v.grid(row=0, column=1, sticky=tk.NS)
        self.scrollbar_h.grid(row=1, column=0, sticky=tk.EW)
        self.sizegrip.grid(row=1, column=1)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

    def onFrameConfigure(self, event):
        """Event handler for when the canvas changes size.

        This usually occurs when the window is resized.
        """
        # Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # adjust the window to fit the app frame
        w = min(self.get_min_app_width(), self.winfo_screenwidth())
        h = min(self.get_min_app_height(), self.winfo_screenheight())
        self.geometry(f"{w}x{h}")

    def onCanvasConfigure(self, event):
        """Event handler for when the frame changes size.

        This usually occurs when the contents of the frame change size.
        """
        # hide the scrollbars when the canvas is large enough to show the whole frame
        if self.canvas.winfo_width() >= self.frame.winfo_reqwidth():
            self.scrollbar_h.grid_remove()
        else:
            self.scrollbar_h.grid()

        if self.canvas.winfo_height() >= self.frame.winfo_reqheight():
            self.scrollbar_v.grid_remove()
        else:
            self.scrollbar_v.grid()

    def get_min_app_width(self):
        """Get minimum width to display entire app."""
        # NOTE: add 2 for the border
        return self.frame.winfo_reqwidth() + self.scrollbar_v.winfo_reqwidth() + 2

    def get_min_app_height(self):
        """Get minimum height to display entire app."""
        # NOTE: add 2 for the border
        return self.frame.winfo_reqheight() + self.scrollbar_h.winfo_reqheight() + 2
