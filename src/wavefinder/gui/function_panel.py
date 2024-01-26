import asyncio
import os
import string
import tkinter as tk
from tkinter import filedialog, ttk

from astropy.time import Time

from ..devices.MightexBufCmos import Camera
from ..functions.sequence import Sequencer
from ..functions.writer import DataWriter
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
        sequencer: Sequencer,
        data_writer: DataWriter,
    ):
        super().__init__(parent, text="Functions", labelanchor=tk.N)
        self.config = config
        self.camera = camera
        self.sequencer = sequencer
        self.data_writer = data_writer

        self.tasks: set[asyncio.Task] = set()

        self.make_capture_buttons_slice()
        self.make_sequence_slice()
        self.make_mode_switch_slice()
        self.make_threshold_slice()
        self.make_image_stats_slice()
        self.make_auto_buttons_slice()
        self.make_focus_slice()

    def make_capture_buttons_slice(self):
        capture_frame = ttk.Frame(self)
        ttk.Label(capture_frame, text="Obs. Type").grid(
            column=0, row=0, padx=10, sticky=tk.E
        )
        self.obstype = tk.StringVar(value=self.config.image_obstypes[0])
        self.obstype_selector = ttk.Combobox(
            capture_frame,
            textvariable=self.obstype,
            values=self.config.image_obstypes,
            state="readonly",
            width=10,
        )
        self.obstype_selector.grid(column=1, row=0, sticky=tk.W)
        self.capture_button_txt = tk.StringVar(value="Capture Image")
        self.capture_button = ttk.Button(
            capture_frame,
            textvariable=self.capture_button_txt,
            command=self.capture,
            width=13,
        )
        self.capture_button.grid(column=2, row=0, padx=10, pady=(10, 0), sticky=tk.E)
        ttk.Label(capture_frame, text="Target Object").grid(
            column=0, row=1, padx=10, sticky=tk.E
        )
        self.target = tk.StringVar()
        self.target_entry = ttk.Entry(capture_frame, textvariable=self.target, width=20)
        self.target_entry.grid(column=1, row=1, sticky=tk.W)
        ttk.Button(capture_frame, text="Save", command=self.save_img, width=13).grid(
            column=2, row=1, padx=10, pady=(10, 0), sticky=tk.E
        )
        capture_frame.grid(column=0, row=0, columnspan=2, pady=10, sticky=tk.E)

    def make_sequence_slice(self):
        sequence_frame = ttk.Frame(self)
        ttk.Label(sequence_frame, text="Automated Sequence").grid(
            column=0, row=0, padx=10, sticky=tk.E
        )
        self.select_sequence_button = ttk.Button(
            sequence_frame,
            text="Select Input File",
            command=self.select_sequence_file,
            width=13,
        )
        self.select_sequence_button.grid(
            column=1, row=0, padx=10, pady=(10, 0), sticky=tk.W
        )
        self.run_sequence_button = ttk.Button(
            sequence_frame, text="Run", command=self.run_sequence, width=13
        )
        self.run_sequence_button.grid(
            column=2, row=0, padx=10, pady=(10, 0), sticky=tk.E
        )
        self.sequence_status = tk.StringVar(value="Need Input File")
        ttk.Label(sequence_frame, textvariable=self.sequence_status).grid(
            column=0, row=1, padx=10, sticky=tk.E
        )
        sequence_frame.grid(column=0, row=1, columnspan=2, pady=10, sticky=tk.E)

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
        ).grid(column=1, row=0)
        ttk.Radiobutton(
            mode_switch_frame,
            text="ROI",
            value=True,
            variable=self.use_roi_stats,
            command=self.set_use_roi_stats,
        ).grid(column=2, row=0)
        mode_switch_frame.grid(column=0, row=2, columnspan=3, pady=10, sticky=tk.W)

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
            threshold_frame,
            text="Set Thresholds",
            width=13,
            command=self.set_thresholds,
        ).grid(column=3, row=0, rowspan=2, sticky=tk.W, pady=10, padx=10)
        threshold_frame.grid(column=0, row=3, columnspan=2, pady=10, sticky=tk.EW)

    def make_image_stats_slice(self):
        self.image_stats_header = tk.StringVar(value="Image Statistics")
        ttk.Label(
            self, textvariable=self.image_stats_header, font="TkDefaultFont 9 underline"
        ).grid(column=0, row=4, sticky=tk.W)
        self.image_stats_txt = tk.StringVar(value="B\nC\nD\nE")
        ttk.Label(self, textvariable=self.image_stats_txt).grid(
            column=0, row=5, rowspan=4, sticky=tk.W
        )

    def make_auto_buttons_slice(self):
        self.center_button = ttk.Button(
            self, text="Auto-Center", width=13, command=self.center
        )
        self.center_button.grid(column=1, row=5, pady=(10, 0), padx=10, sticky=tk.E)
        self.focus_button = ttk.Button(
            self, text="Auto-Focus", width=13, command=self.focus
        )
        self.focus_button.grid(column=1, row=6, pady=(10, 0), padx=10, sticky=tk.E)

    def make_focus_slice(self):
        self.focus_position = tk.StringVar(value="Best Focus: Not Yet Found")
        focus_readout = ttk.Label(self, textvariable=self.focus_position)
        focus_readout.grid(column=0, row=9, sticky=tk.W)

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

        # record obstype and target
        self.config.image_obstype = self.obstype.get()
        self.config.image_target = self.target.get()

    def save_img(self):
        """Save image dialog"""
        # use current date as default filename
        t = Time.now()
        datestr = f"{t.ymdhms[0]:04}{t.ymdhms[1]:02}{t.ymdhms[2]:02}"
        filename = filedialog.asksaveasfilename(
            initialdir="images/",
            initialfile=f"gclef_{datestr}_ait.fits",
            filetypes=(("FITS files", ["*.fits", "*.fts"]), ("all files", "*.*")),
            defaultextension=".fits",
        )
        if filename:
            self.data_writer.write_fits_file(filename, self.config)

    def select_sequence_file(self):
        """Select input file for automated sequence"""
        filename = filedialog.askopenfilename(
            initialfile=f"sequence.csv",
            filetypes=(("CSV files", "*.csv"), ("all files", "*.*")),
        )
        if filename:
            self.sequencer.read_input_file(filename)
            self.sequence_status.set(
                f"Loaded {os.path.basename(filename)}\nReady to Run"
            )

    def run_sequence(self):
        """Run automated sequence

        First select the output directory and make a subdirectory for the data,
        then run the sequence.
        """
        directory = ""
        parent_dir = filedialog.askdirectory(
            title="Select Parent Directory to Save Data", mustexist=False
        )
        if parent_dir:
            # use current date as subdirectory name
            t = Time.now()
            datestr = f"{t.ymdhms[0]:04}{t.ymdhms[1]:02}{t.ymdhms[2]:02}"
            subdir = ""
            # add suffix a, b, c, etc.
            for l in string.ascii_letters:
                subdir = f"{datestr}_{l}"
                try:
                    directory = os.path.join(parent_dir, subdir)
                    os.makedirs(directory)
                    break
                except FileExistsError:
                    # if this one exists, try the next letter
                    continue
        if os.path.exists(directory):
            t, _ = make_task(
                self.sequencer.run_sequence(directory, self.sequence_status), self.tasks
            )
            t.add_done_callback(self.after_sequence)
            self.run_sequence_button.configure(state=tk.DISABLED)
            self.select_sequence_button.configure(state=tk.DISABLED)

    def after_sequence(self, future: asyncio.Future):
        """Callback for after sequence completes"""
        self.run_sequence_button.configure(state=tk.NORMAL)
        self.select_sequence_button.configure(state=tk.NORMAL)

    def focus(self):
        """Start focus routine"""
        t, _ = make_task(self.sequencer.focus(), self.tasks)
        t.add_done_callback(self.after_focus)
        self.focus_button.configure(state=tk.DISABLED)

    def after_focus(self, future: asyncio.Future):
        """Callback for after focus completes"""
        self.focus_position.set(f"Best Focus: {self.config.focus_position:.3f}")
        self.focus_button.configure(state=tk.NORMAL)

    def center(self):
        """Center the image"""
        t, _ = make_task(self.sequencer.center(), self.tasks)
        t.add_done_callback(self.after_center)
        self.center_button.configure(state=tk.DISABLED)

    def after_center(self, future: asyncio.Future):
        """Callback for after center completes"""
        self.center_button.configure(state=tk.NORMAL)

    def update_image_stats_txt(self):
        """Update image statistics"""
        stats_txt = ""

        if self.config.image_use_roi_stats:
            self.image_stats_header.set("Region of Interest Image Statistics")
        else:
            self.image_stats_header.set("Full Frame Image Statistics")

        cen_x = self.config.image_centroid[0]
        cen_y = self.config.image_centroid[1]
        stats_txt += f"Centroid: ({cen_x:.2f}, {cen_y:.2f})\n"
        stats_txt += f"FWHM: {self.config.image_fwhm:.3f}\n"
        stats_txt += f"Max Pixel Value: {self.config.image_max_value}\n"
        stats_txt += f"Saturated Pixels: {self.config.image_n_saturated}"
        self.image_stats_txt.set(stats_txt)

    async def update(self):
        """Update UI"""
        self.update_image_stats_txt()

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()
