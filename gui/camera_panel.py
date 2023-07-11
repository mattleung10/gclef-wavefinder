import asyncio
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np
from PIL import Image, ImageTk

from devices.MightexBufCmos import Camera

from .utils import valid_float, valid_int


class CameraPanel(ttk.LabelFrame):
    """Camera UI Panel"""

    def __init__(self, parent, camera : Camera | None):
        super().__init__(parent, text="Camera", labelanchor=tk.N)

        # UI variables
        self.camera_info1 = tk.StringVar(value="")
        self.camera_info2 = tk.StringVar(value="")
        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_resolution1 = tk.StringVar(value="1280")
        self.camera_resolution2 = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        self.camera_exp_t = tk.StringVar(value="50.0")
        self.camera_fps = tk.StringVar(value="10.0")
        self.camera_gain = tk.StringVar(value="15")
        self.camera_freq = tk.StringVar(value="32")
        self.img_props = tk.StringVar(value="")
        self.freeze_txt = tk.StringVar(value="Freeze")

        # camera variables
        self.camera = camera
        self.frame_img = None
        self.update_resolution = False

        # make panel slices
        self.make_camera_info_slice()
        self.make_camera_mode_slice()
        self.make_camera_resolution_slice()
        self.make_camera_binning_slice()
        self.make_camera_exposure_time_slice()
        self.make_camera_fps_slice()
        self.make_camera_gain_slice()
        self.make_camera_frequency_slice()
        self.make_image_preview_slice()
        self.make_image_properties_slice()
        self.make_buttons()

        # write default settings to camera and update UI to match camera
        self.set_cam_ctrl()

    ### Panel Slices ###
    def make_camera_info_slice(self):
        ttk.Label(self, text="Model").grid(column=0, row=0, sticky=tk.E, padx=10)
        ttk.Label(self, textvariable=self.camera_info1).grid(column=1, row=0,
                                                             columnspan=2, sticky=tk.W)
        ttk.Label(self, text="S/N").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Label(self, textvariable=self.camera_info2).grid(column=1, row=1,
                                                             columnspan=2, sticky=tk.W)
        
    def make_camera_mode_slice(self):
        ttk.Label(self, text="Mode").grid(column=0, row=2, sticky=tk.E, padx=10)
        ttk.Radiobutton(self, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(self, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode).grid(column=2, row=2, sticky=tk.W)
        ttk.Radiobutton(self, text="8 bit", value=8,
                        variable=self.camera_bits).grid(column=1, row=3, sticky=tk.W)
        ttk.Radiobutton(self, text="12 bit", value=12,
                        variable=self.camera_bits, # TODO add 12-bit
                        state=tk.DISABLED).grid(column=2, row=3, sticky=tk.W)
        
    def make_camera_resolution_slice(self):
        ttk.Label(self, text="Resolution").grid(column=0, row=4, sticky=tk.E, padx=10)
        ttk.Entry(self, width=5, textvariable=self.camera_resolution1,
                  validatecommand=(self.register(valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=4, sticky=tk.E)
        ttk.Entry(self, width=5, textvariable=self.camera_resolution2,
                  validatecommand=(self.register(valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=2, row=4, sticky=tk.W)
        
    def make_camera_binning_slice(self):
        ttk.Label(self, text="Binning").grid(column=0, row=5, sticky=tk.E, padx=10)
        ttk.Radiobutton(self, text="No Bin", value=Camera.NO_BIN,
                        variable=self.camera_bin_mode).grid(column=1, row=5,
                                                            columnspan=2, sticky=tk.W)
        ttk.Radiobutton(self, text="1:2", value=Camera.BIN1X2,
                        variable=self.camera_bin_mode).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(self, text="1:3", value=Camera.BIN1X3,
                        variable=self.camera_bin_mode).grid(column=2, row=6, sticky=tk.W)
        ttk.Radiobutton(self, text="1:4", value=Camera.BIN1X4,
                        variable=self.camera_bin_mode).grid(column=1, row=7, sticky=tk.W)
        ttk.Radiobutton(self, text="1:4 skip", value=Camera.SKIP,
                        variable=self.camera_bin_mode).grid(column=2, row=7, sticky=tk.W)
        
    def make_camera_exposure_time_slice(self):
        ttk.Label(self, text="Exp. Time (ms)").grid(column=0, row=8, sticky=tk.E, padx=10)
        ttk.Entry(self, width=5, textvariable=self.camera_exp_t,
                  validatecommand=(self.register(valid_float), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=8, sticky=tk.W)
        
    def make_camera_fps_slice(self):
        ttk.Label(self, text="Frames/Sec").grid(column=0, row=9, sticky=tk.E, padx=10)
        ttk.Entry(self, width=5, textvariable=self.camera_fps,
                  validatecommand=(self.register(valid_float), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=9, sticky=tk.W)

    def make_camera_gain_slice(self):
        ttk.Label(self, text="Gain [6-41]dB").grid(column=0, row=10, sticky=tk.E, padx=10)
        ttk.Entry(self, width=5, textvariable=self.camera_gain,
                  validatecommand=(self.register(valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=10, sticky=tk.W)

    def make_camera_frequency_slice(self):
        ttk.Label(self, text="Frequency (MHz)").grid(column=0, row=11, sticky=tk.E, padx=10)
        ttk.Combobox(self, textvariable=self.camera_freq,
                     values=["32", "16", "8", "4", "2"], state="readonly",
                     width=4).grid(column=1, row=11, sticky=tk.W)
        
    def make_image_preview_slice(self):
        self.preview = ttk.Label(self)
        self.preview.grid(column=3, row=0, columnspan=3, rowspan=12,
                          padx=10, pady=10, sticky=tk.N)

    def make_image_properties_slice(self):
        ttk.Label(self, textvariable=self.img_props).grid(column=6, row=0,
                                                          rowspan=12, sticky=tk.W)

    def make_buttons(self):
        ttk.Button(self, text="Write Config",
                   command=self.set_cam_ctrl).grid(column=0, row=12,
                                                   columnspan=3, pady=(10, 0), padx=10)
        ttk.Button(self, text="Trigger",
                   command=self.snap_img).grid(column=3, row=12, pady=(10, 0), padx=10)

        ttk.Button(self, textvariable=self.freeze_txt,
                   command=self.freeze_preview).grid(column=4, row=12, pady=(10, 0), padx=10)
        ttk.Button(self, text="Save",
                   command=self.save_img).grid(column=5, row=12, pady=(10, 0), padx=10)

    ### Functions ###
    def set_cam_ctrl(self):
        """Set camera to new settings"""
        if self.camera:
            self.camera.set_mode(run_mode=self.camera_run_mode.get(),
                                 # TODO bits=self.camera_bits.get())
                                )
            resolution = ((int(self.camera_resolution1.get()),
                           int(self.camera_resolution2.get())))
            self.camera.set_resolution(resolution=resolution,
                                       bin_mode=self.camera_bin_mode.get())
            self.camera.set_exposure_time(exposure_time=float(self.camera_exp_t.get()))
            self.camera.set_fps(fps=float(self.camera_fps.get()))
            self.camera.set_gain(gain=int(self.camera_gain.get()))
            freq_div = (int.bit_length(32 // int(self.camera_freq.get())) - 1)
            self.camera.set_frequency(freq_mode=freq_div)

            # do the IO task in a thread
            loop = asyncio.get_event_loop()
            t = asyncio.to_thread(self.camera.write_configuration)
            loop.create_task(t)

            # throw out old frames
            self.camera.clear_buffer()

            # update UI to match camera
            self.restore_camera_entries()

    def snap_img(self):
        """Snap an image"""
        if self.camera:
            loop = asyncio.get_event_loop()
            t = asyncio.to_thread(self.camera.trigger)
            loop.create_task(t)

    def restore_camera_entries(self):
        """Restore camera entry boxes from camera
        
        except resolution which is set from update because it
        needs current frame information
        """
        if self.camera:
            loop = asyncio.get_event_loop()
            t = asyncio.to_thread(self.camera.get_camera_info)
            loop.create_task(t).add_done_callback(self.set_camera_info)
            self.camera_exp_t.set(str(self.camera.exposure_time))
            self.camera_fps.set(str(self.camera.fps))
            self.camera_gain.set(str(self.camera.gain))
            self.camera_freq.set(str((32 >> self.camera.freq_mode)))

            # update resolution
            self.update_resolution = True

    def set_camera_info(self, future : asyncio.Future):
        """Update the GUI with the camera info"""
        info = future.result()
        self.camera_info1.set(info["ModuleNo"].strip('\0')) # type: ignore
        self.camera_info2.set(info["SerialNo"].strip('\0')) # type: ignore

    def freeze_preview(self):
        """Freeze preview"""
        if self.freeze_txt.get() == "Freeze":
            self.freeze_txt.set("Unfreeze")
        else:
            self.freeze_txt.set("Freeze")

    def save_img(self):
        """Save image dialog"""
        # TODO: FITS format
        if self.frame_img:
            f = filedialog.asksaveasfilename(initialdir="images/",
                                             initialfile="img.png",
                                             filetypes = (("image files",["*.jpg","*.png"]),
                                                          ("all files","*.*")),
                                             defaultextension=".png")
            if f:
                self.frame_img.save(f)

    async def update(self):
        """Update preview image in viewer"""
        if self.camera:
            await asyncio.to_thread(self.camera.acquire_frames)
            if self.freeze_txt.get() == "Freeze":
                camera_frame = self.camera.get_newest_frame()
                if camera_frame:
                    self.frame_img = Image.fromarray(camera_frame.img)
                    disp_img = ImageTk.PhotoImage(self.frame_img.resize((self.frame_img.width // 4,
                                                                         self.frame_img.height // 4)))
                    self.preview.img = disp_img # type: ignore # protect from garbage collect
                    self.preview.configure(image=disp_img)

                    # update img_props
                    prop_str = ""
                    for p in ["rows", "cols", "bin", "gGain", "expTime", "frameTime",
                            "timestamp", "triggered", "nTriggers", "freq"]:
                        prop_str += str(p) + ': ' + str(getattr(camera_frame, p)) + '\n'
                    self.img_props.set(prop_str.strip())

                    # update resolution, matching newest frame 
                    if self.update_resolution:
                        resolution : tuple[int,int] = self.camera.query_buffer()["resolution"] # type: ignore
                        self.camera_resolution1.set(str(resolution[0]))
                        self.camera_resolution2.set(str(resolution[1]))
                        self.update_resolution = False

        else: # no camera, testing purposes
            if self.freeze_txt.get() == "Freeze":
                self.frame_img = Image.fromarray(np.random.randint(255, size=(960, 1280),
                                                                   dtype=np.uint8)) # random noise
                disp_img = ImageTk.PhotoImage(self.frame_img.resize((self.frame_img.width // 4,
                                                                    self.frame_img.height // 4)))
                self.preview.img = disp_img # type: ignore # protect from garbage collect
                self.preview.configure(image=disp_img)

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            await asyncio.gather(self.update(), asyncio.sleep(interval))