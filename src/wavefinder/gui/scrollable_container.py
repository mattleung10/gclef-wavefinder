import tkinter as tk
from tkinter import ttk


class ScrollableContainer(tk.Tk):
    """A Scrollable Tk App

    Puts a frame inside a canvas with scrollbars.
    Add your elements to the frame.
    """

    def __init__(self):
        super().__init__()

        self.canvas = tk.Canvas(self)
        self.scrollbar_v = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_h = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
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
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.scrollbar_v.grid(row=0, column=1, sticky=tk.NS)
        self.scrollbar_h.grid(row=1, column=0, sticky=tk.EW)
        self.sizegrip.grid(row=1, column=1)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

    def onFrameConfigure(self, event):
        #Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        #Resize the inner frame to match the canvas
        minWidth = self.get_min_width()
        minHeight = self.get_min_height()

        if self.winfo_width() >= minWidth:
            newWidth = self.winfo_width()
            #Hide the scrollbar when not needed
            self.scrollbar_h.grid_remove()
        else:
            newWidth = minWidth
            #Show the scrollbar when needed
            self.scrollbar_h.grid()

        if self.winfo_height() >= minHeight:
            newHeight = self.winfo_height()
            #Hide the scrollbar when not needed
            self.scrollbar_v.grid_remove()
        else:
            newHeight = minHeight
            #Show the scrollbar when needed
            self.scrollbar_v.grid()

        self.canvas.itemconfig(self.window, width=newWidth, height=newHeight)

    def get_min_width(self):
        return self.frame.winfo_reqwidth() + self.scrollbar_v.winfo_reqwidth()
    
    def get_min_height(self):
        return self.frame.winfo_reqheight() + self.scrollbar_h.winfo_reqheight()