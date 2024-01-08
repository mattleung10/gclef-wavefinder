import asyncio
import tkinter as tk
from tkinter import ttk

from ..functions.focus import Focuser
from ..functions.image import variance_to_fwhm
from ..functions.position import Positioner
from ..gui.config import Configuration
from ..gui.utils import Cyclic
from .utils import make_task, valid_float


class FunctionPanel(Cyclic, ttk.LabelFrame):
    """Advanced Function Panel"""

    def __init__(
        self,
        parent: ttk.Frame,
        config: Configuration,
        focuser: Focuser,
        positioner: Positioner,
    ):
        super().__init__(parent, text="Functions", labelanchor=tk.N)
        self.config = config

        # Task variables
        self.tasks: set[asyncio.Task] = set()

        # focus variables
        self.focuser = focuser

        # position variables
        self.positioner = positioner

        self.make_mode_switch_slice()
        self.make_threshold_slice()
        self.make_img_stats_slice()
        self.make_buttons_slice()
        self.make_focus_slice()

        # TODO: function to read in table of positions;
        #       at each position:
        #           move to position
        #           center image
        #           focus
        #           take 3 images: [negative offset, on focus, positive offset]
        #           save images and a table of data

    def make_mode_switch_slice(self):
        self.use_roi_stats = tk.BooleanVar(value=self.config.image_use_roi_stats)
        mode_switch_frame = ttk.Frame(self)
        ttk.Label(mode_switch_frame, text="Calculate using").grid(
            column=0, row=0, rowspan=2, padx=10
        )
        ttk.Radiobutton(
            mode_switch_frame,
            text="Full Frame",
            value=False,
            variable=self.use_roi_stats,
            command=self.set_use_roi_stats,
        ).grid(column=1, row=0, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(
            mode_switch_frame,
            text="ROI",
            value=True,
            variable=self.use_roi_stats,
            command=self.set_use_roi_stats,
        ).grid(column=1, row=1, columnspan=2, sticky=tk.W)
        mode_switch_frame.grid(column=0, row=0, columnspan=3, sticky=tk.W)

    def make_threshold_slice(self):
        self.full_threshold_entry = tk.StringVar(value=str(self.config.image_full_threshold))
        self.roi_threshold_entry = tk.StringVar(value=str(self.config.image_roi_threshold))
        threshold_frame = ttk.Frame(self)
        ttk.Label(threshold_frame, text="Ignore pixel\nvalues below").grid(
            column=0, row=0, rowspan=2, padx=10
        )
        ttk.Entry(
            threshold_frame,
            width=5,
            textvariable=self.full_threshold_entry,
            validatecommand=(self.register(valid_float), "%P"),
            invalidcommand=self.register(self.restore_thresholds),
            validate="focus",
        ).grid(column=1, row=0, sticky=tk.E)
        ttk.Label(threshold_frame, text="% of max in Full Frame").grid(
            column=2, row=0, padx=10, sticky=tk.W
        )
        ttk.Entry(
            threshold_frame,
            width=5,
            textvariable=self.roi_threshold_entry,
            validatecommand=(self.register(valid_float), "%P"),
            invalidcommand=self.register(self.restore_thresholds),
            validate="focus",
        ).grid(column=1, row=1, sticky=tk.E)
        ttk.Label(threshold_frame, text="% of max in ROI").grid(
            column=2, row=1, padx=10, sticky=tk.W
        )
        ttk.Button(
            threshold_frame, text="Set Thresholds", command=self.set_thresholds
        ).grid(column=3, row=0, rowspan=2, sticky=tk.W, pady=10, padx=10)
        threshold_frame.grid(column=0, row=1, columnspan=3)

    def make_img_stats_slice(self):
        self.img_stats_header = tk.StringVar(value="Image Statistics")
        ttk.Label(self, textvariable=self.img_stats_header).grid(column=0, row=2, sticky=tk.W)
        self.img_stats_txt = tk.StringVar(value="B\nC\nD\nE")
        ttk.Label(self, textvariable=self.img_stats_txt).grid(column=0, row=3, rowspan=3, sticky=tk.W)

    def make_buttons_slice(self):
        self.center_button = ttk.Button(self, text="Auto-Center", command=self.center)
        self.center_button.grid(column=1, row=2, pady=(10, 0), padx=10)
        self.focus_button = ttk.Button(self, text="Auto-Focus", command=self.focus)
        self.focus_button.grid(column=1, row=3, pady=(10, 0), padx=10)

    def make_focus_slice(self):
        self.focus_position = tk.StringVar(value="Not Yet Found")
        focus_readout = ttk.Label(self, textvariable=self.focus_position)
        focus_readout.grid(column=2, row=3)

    def set_thresholds(self):
        self.config.image_full_threshold = float(self.full_threshold_entry.get())
        self.config.image_roi_threshold = float(self.roi_threshold_entry.get())

    def set_use_roi_stats(self):
        self.config.image_use_roi_stats = self.use_roi_stats.get()

    def restore_thresholds(self):
        self.full_threshold_entry.set(str(self.config.image_full_threshold))
        self.roi_threshold_entry.set(str(self.config.image_roi_threshold))

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
        self.center_button.configure(state=tk.NORMAL)

    def update_img_stats_txt(self):
        """Update image statistics"""
        stats_txt = ""

        if self.config.image_use_roi_stats:
            self.img_stats_header.set("Region of Interest Image Statistics")
        else:
            self.img_stats_header.set("Full Frame Image Statistics")

        stats_txt += "Centroid: " + str(
            (
                round(self.config.img_stats["cen_x"], 3),
                round(self.config.img_stats["cen_y"], 3),
            )
        )
        stats_txt += "\nFWHM: " + str(
            (
                round(variance_to_fwhm(self.config.img_stats["var_x"]), 3),
                round(variance_to_fwhm(self.config.img_stats["var_y"]), 3),
            )
        )
        stats_txt += "\nMax Pixel Value: " + str(self.config.img_stats["max"])
        stats_txt += "\nSaturated Pixels: " + str(self.config.img_stats["n_sat"])
        self.img_stats_txt.set(stats_txt)

    async def update(self):
        """Update UI"""
        self.update_img_stats_txt()

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()
