import asyncio
import tkinter as tk
from tkinter import ttk

from ..devices.DkMonochromator import DkMonochromator
from .config import Configuration
from .utils import Cyclic, valid_float


class MonochromPanel(Cyclic, ttk.LabelFrame):
    """Monochromater Control Panel"""

    # number of colors must match number of status codes
    COLORS = ["green", "yellow", "red"]
    STATUS = ["OK", "BUSY", "ERROR"]

    def __init__(self, parent: ttk.Frame, config: Configuration, dk: DkMonochromator):
        super().__init__(parent, text="Monochromator", labelanchor=tk.N)
        self.config = config
        self.dk = dk

        self.tasks: set[asyncio.Task] = set()
        self.extra_init = True

        # UI variables
        self.dk_serial = tk.StringVar(self, "Not Found")
        self.status_txt = tk.StringVar(self, MonochromPanel.STATUS[self.dk.status])
        self.status_light = ttk.Label(self, text="Status", width=6)
        self.wavelength_txt = tk.StringVar(self, str(self.dk.current_wavelength))
        self.wavelength_entry = tk.StringVar(self, str(self.dk.target_wavelength))
        self.slit_txt = tk.StringVar(self, str(self.dk.current_slit1) + " / " +  str(self.dk.current_slit2))
        self.slit1_entry = tk.StringVar(self, str(self.dk.target_slit1))
        self.slit2_entry = tk.StringVar(self, str(self.dk.target_slit2))

        self.make_info_slice()
        self.make_wavelength_slice()
        self.make_slit_slice()
        self.make_buttons_slice()

    def make_info_slice(self):
        ttk.Label(self, text="Serial #").grid(column=0, row=0, padx=10, sticky=tk.E)
        ttk.Label(self, textvariable=self.dk_serial).grid(
            column=1, columnspan=2, row=0, sticky=tk.W
        )
        self.status_light.grid(column=3, row=0, padx=10, pady=10)

    def make_wavelength_slice(self):
        ttk.Label(self, text="Wavelength (nm)").grid(
            column=0, row=1, padx=10, sticky=tk.E
        )
        ttk.Label(self, textvariable=self.wavelength_txt).grid(
            column=1, columnspan=2, row=1, padx=10
        )
        ttk.Entry(
            self,
            width=8,
            textvariable=self.wavelength_entry,
            validatecommand=(self.register(valid_float), "%P"),
            invalidcommand=self.register(self.restore_wave_slit_entry),
            validate="focus",
        ).grid(column=3, row=1)

    def make_slit_slice(self):
        ttk.Label(self, text="Slit 1 / 2").grid(column=0, row=2, padx=10, sticky=tk.E)
        ttk.Label(self, textvariable=self.slit_txt).grid(
            column=1, columnspan=2, row=2, padx=10
        )
        ttk.Entry(
            self,
            width=8,
            textvariable=self.slit1_entry,
            validatecommand=(self.register(valid_float), "%P"),
            invalidcommand=self.register(self.restore_wave_slit_entry),
            validate="focus",
        ).grid(column=3, row=2)
        ttk.Entry(
            self,
            width=8,
            textvariable=self.slit2_entry,
            validatecommand=(self.register(valid_float), "%P"),
            invalidcommand=self.register(self.restore_wave_slit_entry),
            validate="focus",
        ).grid(column=4, row=2, sticky=tk.W)

    def make_buttons_slice(self):
        self.jog_less = ttk.Button(self, text="◄", command=self.step_down, width=3)
        self.jog_less.grid(column=1, row=3, pady=(10, 0), padx=2)
        self.jog_more = ttk.Button(self, text="►", command=self.step_up, width=3)
        self.jog_more.grid(column=2, row=3, pady=(10, 0), padx=2)
        g = ttk.Button(self, text="Go", command=self.set_entries)
        g.grid(column=3, row=3, columnspan=2, pady=(10, 0), padx=10)

    def set_entries(self):
        if self.dk.comm_up:
            self.dk.target_wavelength = float(self.wavelength_entry.get())
            self.dk.q.put(self.dk.go_to_target_wavelength)
            self.dk.target_slit1 = float(self.slit1_entry.get())
            self.dk.q.put(self.dk.go_to_slit1)
            self.dk.target_slit2 = float(self.slit2_entry.get())
            self.dk.q.put(self.dk.go_to_slit2)

    def step_up(self):
        """Move grating one step towards IR"""
        if self.dk.comm_up:
            self.dk.q.put(self.dk.step_up)

    def step_down(self):
        """Move grating one step towards UV"""
        if self.dk.comm_up:
            self.dk.q.put(self.dk.step_down)

    def restore_wave_slit_entry(self):
        self.wavelength_entry.set(str(self.dk.target_wavelength))
        self.slit1_entry.set(str(self.dk.target_slit1))
        self.slit2_entry.set(str(self.dk.target_slit2))

    async def update(self):
        """Update UI"""
        # set DK info on first pass
        if (
            self.extra_init
            and self.dk.comm_up
            and self.dk.status == DkMonochromator.READY
        ):
            self.dk_serial.set(str(self.dk.serial_number))
            self.dk.target_wavelength = self.dk.current_wavelength
            self.wavelength_entry.set(str(self.dk.target_wavelength))
            self.dk.target_slit1 = self.dk.current_slit1
            self.slit1_entry.set(str(self.dk.target_slit1))
            self.dk.target_slit2 = self.dk.current_slit2
            self.slit2_entry.set(str(self.dk.target_slit2))
            self.extra_init = False
        self.status_txt.set(MonochromPanel.STATUS[self.dk.status])
        self.status_light.configure(background=MonochromPanel.COLORS[self.dk.status])
        self.wavelength_txt.set(str(self.dk.current_wavelength))
        self.slit_txt.set(str(self.dk.current_slit1) + " / " +  str(self.dk.current_slit2))

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()
