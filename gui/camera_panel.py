import asyncio
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageOps, ImageTk

from devices.MightexBufCmos import Camera, Frame
from functions.image import get_centroid_and_variance, variance_to_fwhm

from .utils import valid_float, valid_int


class CameraPanel():
    """Camera UI Panel is made of 3 LabelFrames"""

    def __init__(self, parent, camera : Camera | None):
        # UI variables
        self.camera_info1 = tk.StringVar(value="")
        self.camera_info2 = tk.StringVar(value="")
        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_res_x = tk.StringVar(value="1280")
        self.camera_res_y = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        self.camera_exp_t = tk.StringVar(value="50.0")
        self.camera_fps = tk.StringVar(value="10.0")
        self.camera_gain = tk.StringVar(value="15")
        self.camera_freq = tk.StringVar(value="32")
        self.img_props = tk.StringVar(value="1\n2\n3\n4\n5\n6\n7\n8\n9\n10")
        self.freeze_txt = tk.StringVar(value="Freeze")
        self.roi_x_entry = tk.StringVar(value="50")
        self.roi_y_entry = tk.StringVar(value="50")
        self.roi_zoom_entry = tk.StringVar(value="10")
        self.img_stats_txt = tk.StringVar(value="A\nB\nC\n")

        # camera variables
        self.camera = camera
        self.full_img = None
        self.roi_img = None
        self.roi_size_x = int(self.roi_x_entry.get())
        self.roi_size_y = int(self.roi_y_entry.get())
        self.roi_zoom = int(self.roi_zoom_entry.get())
        self.img_stats = (0.0, 0.0, 0.0, 0.0, 0.0)
        self.update_resolution_flag = False

        # make panel slices
        settings_frame = ttk.LabelFrame(parent, text="Camera Settings", labelanchor=tk.N)
        self.make_camera_info_slice(settings_frame)
        self.make_camera_mode_slice(settings_frame)
        self.make_camera_resolution_slice(settings_frame)
        self.make_camera_binning_slice(settings_frame)
        self.make_camera_exposure_time_slice(settings_frame)
        self.make_camera_fps_slice(settings_frame)
        self.make_camera_gain_slice(settings_frame)
        self.make_camera_frequency_slice(settings_frame)
        self.make_settings_buttons(settings_frame)
        settings_frame.grid(column=0, row=0, sticky=tk.NSEW)

        full_frame = ttk.LabelFrame(parent, text="Full Frame", labelanchor=tk.N)
        self.make_full_frame_preview_slice(full_frame)
        self.make_image_properties_slice(full_frame)
        self.make_roi_input_slice(full_frame)
        self.make_full_frame_buttons(full_frame)
        self.make_image_stats_slice(full_frame)
        full_frame.grid(column=1, row=0, sticky=tk.NSEW)

        roi_frame = ttk.LabelFrame(parent, text="Region of Interest", labelanchor=tk.N)
        self.make_roi_zoom_slice(roi_frame)
        self.make_roi_preview_slice(roi_frame)
        roi_frame.grid(column=2, row=0, sticky=tk.NSEW)

        # write default settings to camera and update UI to match camera
        self.set_cam_ctrl()

    ### Camera Settings Slices ###
    def make_camera_info_slice(self, parent):
        ttk.Label(parent, text="Model").grid(column=0, row=0, sticky=tk.E, padx=10)
        ttk.Label(parent, textvariable=self.camera_info1).grid(column=1, row=0,
                                                             columnspan=2, sticky=tk.W)
        ttk.Label(parent, text="S/N").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Label(parent, textvariable=self.camera_info2).grid(column=1, row=1,
                                                             columnspan=2, sticky=tk.W)
        
    def make_camera_mode_slice(self, parent):
        ttk.Label(parent, text="Mode").grid(column=0, row=2, sticky=tk.E, padx=10)
        ttk.Radiobutton(parent, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(parent, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode).grid(column=2, row=2, sticky=tk.W)
        ttk.Radiobutton(parent, text="8 bit", value=8,
                        variable=self.camera_bits).grid(column=1, row=3, sticky=tk.W)
        ttk.Radiobutton(parent, text="12 bit", value=12,
                        variable=self.camera_bits, # TODO add 12-bit
                        state=tk.DISABLED).grid(column=2, row=3, sticky=tk.W)
        
    def make_camera_resolution_slice(self, parent):
        ttk.Label(parent, text="Resolution").grid(column=0, row=4, sticky=tk.E, padx=10)
        ttk.Entry(parent, width=5, textvariable=self.camera_res_x,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=parent.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=4, sticky=tk.E)
        ttk.Entry(parent, width=5, textvariable=self.camera_res_y,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=parent.register(self.restore_camera_entries),
                  validate='focus').grid(column=2, row=4, sticky=tk.W)
        
    def make_camera_binning_slice(self, parent):
        ttk.Label(parent, text="Binning").grid(column=0, row=5, sticky=tk.E, padx=10)
        ttk.Radiobutton(parent, text="No Bin", value=Camera.NO_BIN,
                        variable=self.camera_bin_mode).grid(column=1, row=5,
                                                            columnspan=2, sticky=tk.W)
        ttk.Radiobutton(parent, text="1:2", value=Camera.BIN1X2,
                        variable=self.camera_bin_mode).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(parent, text="1:3", value=Camera.BIN1X3,
                        variable=self.camera_bin_mode).grid(column=2, row=6, sticky=tk.W)
        ttk.Radiobutton(parent, text="1:4", value=Camera.BIN1X4,
                        variable=self.camera_bin_mode).grid(column=1, row=7, sticky=tk.W)
        ttk.Radiobutton(parent, text="1:4 skip", value=Camera.SKIP,
                        variable=self.camera_bin_mode).grid(column=2, row=7, sticky=tk.W)
        
    def make_camera_exposure_time_slice(self, parent):
        ttk.Label(parent, text="Exp. Time (ms)").grid(column=0, row=8, sticky=tk.E, padx=10)
        ttk.Entry(parent, width=5, textvariable=self.camera_exp_t,
                  validatecommand=(parent.register(valid_float), '%P'),
                  invalidcommand=parent.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=8, sticky=tk.W)
        
    def make_camera_fps_slice(self, parent):
        ttk.Label(parent, text="Frames/Sec").grid(column=0, row=9, sticky=tk.E, padx=10)
        ttk.Entry(parent, width=5, textvariable=self.camera_fps,
                  validatecommand=(parent.register(valid_float), '%P'),
                  invalidcommand=parent.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=9, sticky=tk.W)

    def make_camera_gain_slice(self, parent):
        ttk.Label(parent, text="Gain [6-41]dB").grid(column=0, row=10, sticky=tk.E, padx=10)
        ttk.Entry(parent, width=5, textvariable=self.camera_gain,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=parent.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=10, sticky=tk.W)

    def make_camera_frequency_slice(self, parent):
        ttk.Label(parent, text="Frequency (MHz)").grid(column=0, row=11, sticky=tk.E, padx=10)
        ttk.Combobox(parent, textvariable=self.camera_freq,
                     values=["32", "16", "8", "4", "2"], state="readonly",
                     width=4).grid(column=1, row=11, sticky=tk.W)
        
    def make_settings_buttons(self, parent):
        b = ttk.Button(parent, text="Write Config", command=self.set_cam_ctrl)
        b.grid(column=0, row=12, columnspan=3, pady=(10, 0), padx=10, sticky=tk.S)

    ### Full Frame Slices ###
    def make_full_frame_preview_slice(self, parent):
        self.full_frame_preview = ttk.Label(parent)
        self.full_frame_preview.grid(column=0, row=0, columnspan=3, rowspan=13, sticky=tk.N)

    def make_image_properties_slice(self, parent):
        l = ttk.Label(parent, textvariable=self.img_props)
        l.grid(column=3, row=0, rowspan=10, columnspan=2, padx=10, sticky=tk.NW)

    def make_roi_input_slice(self, parent):
        ttk.Label(parent, text="Region of Interest").grid(column=3, row=11,
                                                          columnspan=2, padx=10)
        ttk.Entry(parent, width=5, textvariable=self.roi_x_entry,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=(parent.register(self.roi_x_entry.set), self.camera_res_x.get()),
                  validate='focus').grid(column=3, row=12, sticky=tk.E)
        ttk.Entry(parent, width=5, textvariable=self.roi_y_entry,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=(parent.register(self.roi_y_entry.set), self.camera_res_y.get()),
                  validate='focus').grid(column=4, row=12, sticky=tk.W)
        ttk.Button(parent, text="Set ROI",
                   command=self.set_roi).grid(column=3, row=13, pady=(10, 0), columnspan=2)

    def make_full_frame_buttons(self, parent):
        ttk.Button(parent, text="Trigger",
                   command=self.snap_img).grid(column=0, row=13, pady=(10, 0), padx=10)
        ttk.Button(parent, textvariable=self.freeze_txt,
                   command=self.freeze_preview).grid(column=1, row=13, pady=(10, 0), padx=10)
        ttk.Button(parent, text="Save",
                   command=self.save_img).grid(column=2, row=13, pady=(10, 0), padx=10)
        
    def make_image_stats_slice(self, parent):
        ttk.Label(parent, textvariable=self.img_stats_txt).grid(column=0, row=14,
                                                            columnspan=3, sticky=tk.W)
        
    ### ROI Frame Slices ###
    def make_roi_zoom_slice(self, parent):
        zoom_frame = ttk.Frame(parent)
        ttk.Label(zoom_frame, text="ROI Zoom").grid(column=0, row=0, padx=10)
        ttk.Entry(zoom_frame, width=4, textvariable=self.roi_zoom_entry,
                  validatecommand=(parent.register(valid_int), '%P'),
                  invalidcommand=(parent.register(self.roi_zoom_entry.set), str(1)),
                  validate='focus').grid(column=0, row=1)
        ttk.Button(zoom_frame, text="Set Zoom",
                   command=self.set_roi_zoom).grid(column=0, row=2, pady=(10, 0))
        zoom_frame.grid(column=0, row=0, sticky=tk.N)

    def make_roi_preview_slice(self, parent):
        self.roi_preview = ttk.Label(parent)
        self.roi_preview.grid(column=1, row=0, rowspan=3)

    ### Functions ###
    def set_cam_ctrl(self):
        """Set camera to new settings"""
        if self.camera:
            self.camera.set_mode(run_mode=self.camera_run_mode.get(),
                                 # TODO bits=self.camera_bits.get())
                                )
            resolution = ((int(self.camera_res_x.get()),
                           int(self.camera_res_y.get())))
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
            self.update_resolution_flag = True

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
        if self.full_img:
            f = filedialog.asksaveasfilename(initialdir="images/",
                                             initialfile="img.png",
                                             filetypes = (("image files",["*.jpg","*.png"]),
                                                          ("all files","*.*")),
                                             defaultextension=".png")
            if f:
                self.full_img.save(f)

    def set_roi(self):
        """Set the region of interest"""

        # get inputs and clip to valid,
        # then write back valid values
        size_x = int(self.roi_x_entry.get())
        size_y = int(self.roi_y_entry.get())
        size_x = np.clip(size_x, 1, int(self.camera_res_x.get()))
        size_y = np.clip(size_y, 1, int(self.camera_res_y.get()))
        self.roi_size_x = size_x
        self.roi_size_y = size_y
        self.roi_x_entry.set(str(size_x))
        self.roi_y_entry.set(str(size_y))

    def set_roi_zoom(self):
        """Set the ROI zoom"""
        self.roi_zoom = int(self.roi_zoom_entry.get())
        self.update_roi_img()

    def get_roi_box(self):
        """Return the (left, lower, right, upper)
        box representing the region of interest
        """
        if self.full_img:
            size_x = self.roi_size_x
            size_y = self.roi_size_y
            f_size_x = self.full_img.size[0]
            f_size_y = self.full_img.size[1]
            left = f_size_x//2 - size_x//2
            lower = f_size_y//2 - size_y//2
            box = (left, lower, left+size_x, lower+size_y)
            return box
        else:
            return (0,0,0,0)

    def update_roi_img(self):
        """Update the region of interest image"""
        if self.full_img:
            box = self.get_roi_box()
            # crop to ROI, then blow up ROI by zoom factor
            x = box[2] - box[0]
            y = box[3] - box[1]
            z = self.roi_zoom
            self.roi_img = self.full_img.crop(box)
            zoomed = self.roi_img.resize(size=(z*x, z*y), resample=Image.Resampling.NEAREST)
            disp_img = ImageTk.PhotoImage(zoomed)
            self.roi_preview.img = disp_img # type: ignore # protect from garbage collect
            self.roi_preview.configure(image=disp_img)

    def update_img_props(self, camera_frame : Frame):
        """Update image properties"""
        prop_str = ""
        for p in ["rows", "cols", "bin", "gGain", "expTime", "frameTime",
                  "timestamp", "triggered", "nTriggers", "freq"]:
            prop_str += str(p) + ': ' + str(getattr(camera_frame, p)) + '\n'
        self.img_props.set(prop_str.strip())

    def update_img_stats(self):
        """Update image statistics"""
        if self.full_img:
            stats = ""
            self.img_stats = get_centroid_and_variance(self.full_img)
            stats += "Centroid: " + str(tuple(map(lambda v: round(v, 3), self.img_stats[0:2])))
            stats += "\nVariance: " + str(tuple(map(lambda v: round(v, 3), self.img_stats[2:])))
            stats += "\nStd Dev: " + str(tuple(map(lambda v: round(np.sqrt(v), 3), self.img_stats[2:4])))
            stats += "\nFWHM: " + str(tuple(map(lambda v: round(variance_to_fwhm(v), 3), self.img_stats[2:4])))
            self.img_stats_txt.set(stats)

    def update_full_frame_preview(self):
        """Update the full frame preview"""
        if self.full_img:
            # draw roi box
            roi_box = self.get_roi_box()
            img = self.full_img.convert("RGB")
            ImageDraw.Draw(img).rectangle(roi_box, width=3, outline=ImageColor.getrgb("yellow"))
            # draw FWHM
            c = self.img_stats
            x_hwhm = variance_to_fwhm(c[2]) / 2
            y_hwhm = variance_to_fwhm(c[3]) / 2 
            ImageDraw.Draw(img).ellipse((c[0]-x_hwhm, c[1]-y_hwhm, c[0]+x_hwhm, c[1]+y_hwhm),
                                        width=3, outline=ImageColor.getrgb("red"))

            # display
            disp_img = ImageTk.PhotoImage(img.resize((img.width // 4, img.height // 4)))
            self.full_frame_preview.img = disp_img # type: ignore # protect from garbage collect
            self.full_frame_preview.configure(image=disp_img)

    def update_resolution(self):
        """Update resolution from camera, matching newest frame """
        resolution : tuple[int,int] = self.camera.query_buffer()["resolution"] # type: ignore
        self.camera_res_x.set(str(resolution[0]))
        self.camera_res_y.set(str(resolution[1]))
        self.update_resolution_flag = False

    async def update(self):
        """Update preview image in viewer"""
        if self.camera:
            await asyncio.to_thread(self.camera.acquire_frames)
            if self.freeze_txt.get() == "Freeze":
                camera_frame = self.camera.get_newest_frame()
                if camera_frame:
                    self.full_img = Image.fromarray(camera_frame.img)
                    self.update_img_props(camera_frame)
                    if self.update_resolution_flag:
                        self.update_resolution()
        else: # no camera, testing purposes
            if self.freeze_txt.get() == "Freeze":
                # image components
                # noise = Image.effect_noise(size=(1280, 960), sigma=100)
                black = Image.fromarray(np.zeros((960, 1280))) # np and image dimensions are flipped
                gradient = ImageOps.invert(Image.radial_gradient(mode='L'))
                # set image to black and then paste in the gradient at specified position
                # self.full_img = noise
                self.full_img = black
                self.full_img.paste(gradient, (85,400))

        self.update_img_stats()
        self.update_full_frame_preview()
        self.update_roi_img()

    async def update_loop(self, interval : float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            await asyncio.gather(self.update(), asyncio.sleep(interval))