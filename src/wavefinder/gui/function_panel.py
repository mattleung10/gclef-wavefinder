import asyncio
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from ..functions.writer import DataWriter
from ..devices.MightexBufCmos import Camera
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
        camera: Camera | None,
        focuser: Focuser,
        positioner: Positioner,
        data_writer: DataWriter,
    ):
        super().__init__(parent, text="Functions", labelanchor=tk.N)
        self.config = config
        self.camera = camera
        self.focuser = focuser
        self.positioner = positioner
        self.data_writer = data_writer

        # Task variables
        self.tasks: set[asyncio.Task] = set()

        self.make_capture_buttons_slice()
        self.make_mode_switch_slice()
        self.make_threshold_slice()
        self.make_img_stats_slice()
        self.make_auto_buttons_slice()
        self.make_focus_slice()

        # TODO: function to read in table of positions;
        #       at each position:
        #           move to position
        #           center image
        #           focus
        #           take 3 images: [negative offset, on focus, positive offset]
        #           save images and a table of data

    def make_capture_buttons_slice(self):
        capture_frame = ttk.Frame(self)
        self.capture_button_txt = tk.StringVar(value="Capture Image")
        self.capture_button = ttk.Button(
            capture_frame, textvariable=self.capture_button_txt, command=self.capture
        )
        self.capture_button.grid(column=0, row=0, padx=10)
        ttk.Button(capture_frame, text="Save", command=self.save_img).grid(
            column=2, row=0, padx=10
        )
        capture_frame.grid(column=0, row=0, columnspan=3, pady=10)

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
        mode_switch_frame.grid(column=0, row=1, columnspan=3, sticky=tk.W)

    def make_threshold_slice(self):
        self.full_threshold_entry = tk.StringVar(
            value=str(self.config.image_full_threshold)
        )
        self.roi_threshold_entry = tk.StringVar(
            value=str(self.config.image_roi_threshold)
        )
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
        threshold_frame.grid(column=0, row=2, columnspan=2)

    def make_img_stats_slice(self):
        self.img_stats_header = tk.StringVar(value="Image Statistics")
        ttk.Label(
            self, textvariable=self.img_stats_header, font="TkDefaultFont 9 underline"
        ).grid(column=0, row=3, sticky=tk.W)
        self.img_stats_txt = tk.StringVar(value="B\nC\nD\nE")
        ttk.Label(self, textvariable=self.img_stats_txt).grid(
            column=0, row=4, rowspan=4, sticky=tk.W
        )

    def make_auto_buttons_slice(self):
        self.center_button = ttk.Button(self, text="Auto-Center", command=self.center)
        self.center_button.grid(column=1, row=4, pady=(10, 0), padx=10, sticky=tk.E)
        self.focus_button = ttk.Button(self, text="Auto-Focus", command=self.focus)
        self.focus_button.grid(column=1, row=5, pady=(10, 0), padx=10, sticky=tk.E)

    def make_focus_slice(self):
        self.focus_position = tk.StringVar(value="Best Focus: Not Yet Found")
        focus_readout = ttk.Label(self, textvariable=self.focus_position)
        focus_readout.grid(column=0, row=8, sticky=tk.W)

    def set_thresholds(self):
        self.config.image_full_threshold = float(self.full_threshold_entry.get())
        self.config.image_roi_threshold = float(self.roi_threshold_entry.get())

    def set_use_roi_stats(self):
        self.config.image_use_roi_stats = self.use_roi_stats.get()

    def restore_thresholds(self):
        self.full_threshold_entry.set(str(self.config.image_full_threshold))
        self.roi_threshold_entry.set(str(self.config.image_roi_threshold))

    def capture(self):
        """Capture an image

        If camera is in trigger mode, send the trigger; otherwise, freeze the image.
        """
        if self.config.camera_run_mode == Camera.TRIGGER:
            if self.camera:
                make_task(self.camera.trigger(), self.tasks)
        else:
            if self.config.image_frozen:
                self.config.image_frozen = False
                self.capture_button_txt.set("Capture Image")
            else:
                self.config.image_frozen = True
                self.capture_button_txt.set("Resume")

    def save_img(self):
        """Save image dialog"""
        f = filedialog.asksaveasfilename(
            initialdir="images/",
            initialfile="new.fits",
            filetypes=(("FITS files", ["*.fits", "*.fts"]), ("all files", "*.*")),
            defaultextension=".fits",
        )
        if f:
            if self.config.camera_frame:
                self.data_writer.write_fits_file(f, frame=self.config.camera_frame)
            else:
                self.data_writer.write_fits_file(f, image=self.config.full_img)

    def focus(self):
        """Start focus routine"""
        t, _ = make_task(self.focuser.focus(), self.tasks)
        t.add_done_callback(self.after_focus)
        self.focus_button.configure(state=tk.DISABLED)

    def after_focus(self, future: asyncio.Future):
        """Callback for after focus completes"""
        self.focus_position.set(f"Best Focus: {future.result():.3f}")
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

        cen_x = self.config.img_stats["cen_x"]
        cen_y = self.config.img_stats["cen_y"]
        fwhm_x = variance_to_fwhm(self.config.img_stats["var_x"])
        fwhm_y = variance_to_fwhm(self.config.img_stats["var_y"])
        stats_txt += "Centroid: " + f"({cen_x:.2f}, {cen_y:.2f})"
        stats_txt += "\nFWHM: " + f"({fwhm_x:.3f}, {fwhm_y:.3f})"
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
