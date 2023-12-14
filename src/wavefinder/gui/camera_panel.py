import asyncio
import tkinter as tk
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageOps, ImageTk

from ..devices.MightexBufCmos import Camera, Frame
from ..functions.image import get_centroid_and_variance, variance_to_fwhm
from ..functions.writer import DataWriter
from ..gui.utils import Cyclic
from .utils import make_task, valid_float, valid_int

if TYPE_CHECKING:
    from .app import App


class CameraPanel(Cyclic):
    """Camera UI Panel is made of 3 LabelFrames"""

    def __init__(self, parent: "App", camera: Camera | None, data_writer: DataWriter):
        # Task variables
        self.tasks: set[asyncio.Task] = set()
        self.extra_init = True

        # UI variables
        self.camera_model = tk.StringVar(value="")
        self.camera_serial = tk.StringVar(value="")
        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_res_x = tk.StringVar(value="1280")
        self.camera_res_y = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        self.camera_exp_t = tk.StringVar(value="50.0")
        self.camera_fps = tk.StringVar(value="10.0")
        self.camera_gain = tk.StringVar(value="15")
        self.camera_freq = tk.StringVar(value="32")
        self.img_props = tk.StringVar(value="1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11")
        self.freeze_txt = tk.StringVar(value="Freeze")
        self.roi_x_entry = tk.StringVar(value="50")
        self.roi_y_entry = tk.StringVar(value="50")
        self.roi_zoom_entry = tk.StringVar(value="10")
        self.img_stats_txt = tk.StringVar(value="A\nB\nC\n")

        # camera variables
        self.camera = camera
        res = (int(self.camera_res_x.get()), int(self.camera_res_y.get()))
        self.camera_frame = None
        self.full_img = Image.new(mode="L", size=res, color=0)
        self.roi_size_x = int(self.roi_x_entry.get())
        self.roi_size_y = int(self.roi_y_entry.get())
        self.roi_zoom = int(self.roi_zoom_entry.get())
        self.img_stats = (0.0, 0.0, 0.0, 0.0, 0.0)
        self.update_resolution_flag = False

        self.data_writer = data_writer

        # make panel slices
        settings_frame = ttk.LabelFrame(
            parent, text="Camera Settings", labelanchor=tk.N
        )
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
        self.make_full_frame_buttons(full_frame)
        self.make_image_stats_slice(full_frame)
        self.make_histogram(full_frame)
        full_frame.grid(column=1, row=0, sticky=tk.NSEW)

        roi_frame = ttk.LabelFrame(parent, text="Region of Interest", labelanchor=tk.N)
        self.make_roi_input_slice(roi_frame)
        self.make_roi_preview_slice(roi_frame)
        roi_frame.grid(column=2, row=0, rowspan=2, sticky=tk.NSEW)

        # update UI to match camera object
        self.restore_camera_entries()
        # write settings to camera and then update UI to match camera object
        self.set_cam_ctrl()

    ### Camera Settings Slices ###
    def make_camera_info_slice(self, parent):
        ttk.Label(parent, text="Model").grid(column=0, row=0, sticky=tk.E, padx=10)
        ttk.Label(parent, textvariable=self.camera_model).grid(
            column=1, row=0, columnspan=2, sticky=tk.W
        )
        ttk.Label(parent, text="Serial").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Label(parent, textvariable=self.camera_serial).grid(
            column=1, row=1, columnspan=2, sticky=tk.W
        )

    def make_camera_mode_slice(self, parent):
        ttk.Label(parent, text="Mode").grid(column=0, row=2, sticky=tk.E, padx=10)
        ttk.Radiobutton(
            parent, text="Stream", value=Camera.NORMAL, variable=self.camera_run_mode
        ).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="Trigger", value=Camera.TRIGGER, variable=self.camera_run_mode
        ).grid(column=2, row=2, sticky=tk.W)
        ttk.Radiobutton(parent, text="8 bit", value=8, variable=self.camera_bits).grid(
            column=1, row=3, sticky=tk.W
        )
        ttk.Radiobutton(
            parent, text="12 bit", value=12, variable=self.camera_bits
        ).grid(column=2, row=3, sticky=tk.W)

    def make_camera_resolution_slice(self, parent):
        ttk.Label(parent, text="Resolution").grid(column=0, row=4, sticky=tk.E, padx=10)
        ttk.Entry(
            parent,
            width=5,
            textvariable=self.camera_res_x,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=parent.register(self.restore_camera_entries),
            validate="focus",
        ).grid(column=1, row=4, sticky=tk.E)
        ttk.Entry(
            parent,
            width=5,
            textvariable=self.camera_res_y,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=parent.register(self.restore_camera_entries),
            validate="focus",
        ).grid(column=2, row=4, sticky=tk.W)

    def make_camera_binning_slice(self, parent):
        ttk.Label(parent, text="Binning").grid(column=0, row=5, sticky=tk.E, padx=10)
        ttk.Radiobutton(
            parent, text="No Bin", value=Camera.NO_BIN, variable=self.camera_bin_mode
        ).grid(column=1, row=5, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="1:2", value=Camera.BIN1X2, variable=self.camera_bin_mode
        ).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="1:3", value=Camera.BIN1X3, variable=self.camera_bin_mode
        ).grid(column=2, row=6, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="1:4", value=Camera.BIN1X4, variable=self.camera_bin_mode
        ).grid(column=1, row=7, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="1:4 skip", value=Camera.SKIP, variable=self.camera_bin_mode
        ).grid(column=2, row=7, sticky=tk.W)

    def make_camera_exposure_time_slice(self, parent):
        ttk.Label(parent, text="Exp. Time (ms)").grid(
            column=0, row=8, sticky=tk.E, padx=10
        )
        ttk.Entry(
            parent,
            width=5,
            textvariable=self.camera_exp_t,
            validatecommand=(parent.register(valid_float), "%P"),
            invalidcommand=parent.register(self.restore_camera_entries),
            validate="focus",
        ).grid(column=1, row=8, sticky=tk.W)

    def make_camera_fps_slice(self, parent):
        ttk.Label(parent, text="Frames/Sec").grid(column=0, row=9, sticky=tk.E, padx=10)
        ttk.Entry(
            parent,
            width=5,
            textvariable=self.camera_fps,
            validatecommand=(parent.register(valid_float), "%P"),
            invalidcommand=parent.register(self.restore_camera_entries),
            validate="focus",
        ).grid(column=1, row=9, sticky=tk.W)

    def make_camera_gain_slice(self, parent):
        ttk.Label(parent, text="Gain [6-41]dB").grid(
            column=0, row=10, sticky=tk.E, padx=10
        )
        ttk.Entry(
            parent,
            width=5,
            textvariable=self.camera_gain,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=parent.register(self.restore_camera_entries),
            validate="focus",
        ).grid(column=1, row=10, sticky=tk.W)

    def make_camera_frequency_slice(self, parent):
        ttk.Label(parent, text="Frequency (MHz)").grid(
            column=0, row=11, sticky=tk.E, padx=10
        )
        ttk.Combobox(
            parent,
            textvariable=self.camera_freq,
            values=["32", "16", "8", "4", "2"],
            state="readonly",
            width=4,
        ).grid(column=1, row=11, sticky=tk.W)

    def make_settings_buttons(self, parent):
        b = ttk.Button(parent, text="Write Config", command=self.set_cam_ctrl)
        b.grid(column=0, row=12, columnspan=3, pady=(10, 0), padx=10, sticky=tk.S)

    ### Full Frame Slices ###
    def make_full_frame_preview_slice(self, parent):
        self.full_frame_preview = ttk.Label(parent)
        self.full_frame_preview.grid(
            column=0, row=0, columnspan=3, rowspan=13, sticky=tk.N
        )

    def make_image_properties_slice(self, parent):
        l = ttk.Label(parent, textvariable=self.img_props)
        l.grid(column=3, row=0, rowspan=11, columnspan=2, padx=10, sticky=tk.NW)

    def make_full_frame_buttons(self, parent):
        ttk.Button(parent, text="Trigger", command=self.snap_img).grid(
            column=0, row=13, pady=(10, 0), padx=10
        )
        ttk.Button(
            parent, textvariable=self.freeze_txt, command=self.freeze_preview
        ).grid(column=1, row=13, pady=(10, 0), padx=10)
        ttk.Button(parent, text="Save", command=self.save_img).grid(
            column=2, row=13, pady=(10, 0), padx=10
        )

    def make_image_stats_slice(self, parent):
        ttk.Label(parent, textvariable=self.img_stats_txt).grid(
            column=0, row=14, columnspan=3, sticky=tk.W
        )
        # NOTE secret reset button
        # ttk.Button(parent, text="Reset",
        #            command=self.reset_camera).grid(column=4, row=14, pady=(10, 0), padx=10)

    def make_histogram(self, parent):
        self.histogram = tk.Canvas(parent, width=500, height=200)
        self.histogram.grid(column=0, row=15, columnspan=3)

    ### ROI Frame Slices ###
    def make_roi_input_slice(self, parent):
        input_frame = ttk.Frame(parent)
        ttk.Label(input_frame, text="Bounds").grid(column=0, row=0, padx=10)
        ttk.Entry(
            input_frame,
            width=5,
            textvariable=self.roi_x_entry,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=(
                parent.register(self.roi_x_entry.set),
                self.camera_res_x.get(),
            ),
            validate="focus",
        ).grid(column=1, row=0, sticky=tk.E)
        ttk.Entry(
            input_frame,
            width=5,
            textvariable=self.roi_y_entry,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=(
                parent.register(self.roi_y_entry.set),
                self.camera_res_y.get(),
            ),
            validate="focus",
        ).grid(column=2, row=0, sticky=tk.W)
        ttk.Label(input_frame, text="Zoom").grid(column=0, row=1, padx=10)
        ttk.Entry(
            input_frame,
            width=5,
            textvariable=self.roi_zoom_entry,
            validatecommand=(parent.register(valid_int), "%P"),
            invalidcommand=(parent.register(self.roi_zoom_entry.set), str(1)),
            validate="focus",
        ).grid(column=1, row=1, sticky=tk.E)
        ttk.Button(input_frame, text="Set", command=self.set_roi).grid(
            column=1, row=2, pady=(10, 0), columnspan=2, padx=10
        )
        input_frame.grid(column=0, row=0, rowspan=2, sticky=tk.NW)

    def make_roi_preview_slice(self, parent):
        roi_prev_frame = ttk.Frame(parent)
        self.roi_preview = ttk.Label(roi_prev_frame)
        self.roi_preview.grid(column=0, row=0)
        # cross-cuts
        self.cc_x = tk.Canvas(roi_prev_frame)
        self.cc_x.grid(column=0, row=1)
        self.cc_y = tk.Canvas(roi_prev_frame)
        self.cc_y.grid(column=1, row=0)
        roi_prev_frame.grid(column=1, row=0)

    ### Functions ###
    def set_cam_ctrl(self):
        """Set camera to new settings"""
        if self.camera:
            make_task(self.set_cam_ctrl_async(), self.tasks)

    async def set_cam_ctrl_async(self):
        if self.camera:
            # set up camera object
            await self.camera.set_mode(
                run_mode=self.camera_run_mode.get(), bits=self.camera_bits.get()
            )
            resolution = (int(self.camera_res_x.get()), int(self.camera_res_y.get()))
            await self.camera.set_resolution(
                resolution=resolution, bin_mode=self.camera_bin_mode.get()
            )
            await self.camera.set_exposure_time(
                exposure_time=float(self.camera_exp_t.get())
            )
            await self.camera.set_fps(fps=float(self.camera_fps.get()))
            await self.camera.set_gain(gain=int(self.camera_gain.get()))
            freq_div = int.bit_length(32 // int(self.camera_freq.get())) - 1
            await self.camera.set_frequency(freq_mode=freq_div)

            # write to camera, clear buffer, update UI
            await self.camera.write_configuration()
            await self.camera.clear_buffer()
            self.restore_camera_entries()

    def snap_img(self):
        """Snap an image"""
        if self.camera:
            make_task(self.camera.trigger(), self.tasks)

    def restore_camera_entries(self):
        """Restore camera entry boxes from camera

        except resolution which is set from update because it
        needs current frame information
        """
        if self.camera:
            self.camera_run_mode.set(self.camera.run_mode)
            self.camera_bin_mode.set(self.camera.bin_mode)
            self.camera_exp_t.set(str(self.camera.exposure_time))
            self.camera_fps.set(str(self.camera.fps))
            self.camera_gain.set(str(self.camera.gain))
            self.camera_freq.set(str((32 >> self.camera.freq_mode)))

            # update resolution
            self.update_resolution_flag = True

    def set_camera_info(self, info: dict[str, str]):
        """Update the GUI with the camera info"""
        self.camera_model.set(info["ModuleNo"])
        self.camera_serial.set(info["SerialNo"])

    def freeze_preview(self):
        """Freeze preview"""
        if self.freeze_txt.get() == "Freeze":
            self.freeze_txt.set("Unfreeze")
        else:
            self.freeze_txt.set("Freeze")

    def save_img(self):
        """Save image dialog"""
        f = filedialog.asksaveasfilename(
            initialdir="images/",
            initialfile="new.fits",
            filetypes=(("FITS files", ["*.fits", "*.fts"]), ("all files", "*.*")),
            defaultextension=".fits",
        )
        if f:
            if self.camera_frame:
                self.data_writer.write_fits_file(f, frame=self.camera_frame)
            else:
                self.data_writer.write_fits_file(f, image=self.full_img)

    def reset_camera(self):
        if self.camera:
            make_task(self.camera.reset(), self.tasks)

    def set_roi(self):
        """Set the region of interest bounds and zoom"""

        # get inputs and clip to valid, then write back valid values
        size_x = int(self.roi_x_entry.get())
        size_y = int(self.roi_y_entry.get())
        size_x = min(max(size_x, 1), int(self.camera_res_x.get()))
        size_y = min(max(size_y, 1), int(self.camera_res_y.get()))
        self.roi_size_x = size_x
        self.roi_size_y = size_y
        self.roi_x_entry.set(str(size_x))
        self.roi_y_entry.set(str(size_y))
        self.roi_zoom = int(self.roi_zoom_entry.get())
        self.update_full_frame_preview()
        self.update_roi_img()

    def get_roi_box(self) -> tuple[int, int, int, int]:
        """Return the (left, lower, right, upper)
        box representing the region of interest
        """
        size_x = self.roi_size_x
        size_y = self.roi_size_y
        f_size_x = self.full_img.size[0]
        f_size_y = self.full_img.size[1]
        left = f_size_x // 2 - size_x // 2
        lower = f_size_y // 2 - size_y // 2
        box = (left, lower, left + size_x, lower + size_y)
        return box

    def update_roi_img(self):
        """Update the region of interest image"""
        box = self.get_roi_box()
        # crop to ROI, then blow up ROI by zoom factor
        x = box[2] - box[0]
        y = box[3] - box[1]
        z = self.roi_zoom
        roi_img = self.full_img.crop(box)
        zoomed = roi_img.resize(
            size=(z * x, z * y), resample=Image.Resampling.NEAREST
        ).convert("RGB")
        # draw crosshairs
        ImageDraw.Draw(zoomed).line(
            [(0, z * (y // 2) + z // 2), (z * x, z * (y // 2) + z // 2)],
            fill=ImageColor.getrgb("yellow"),
        )
        ImageDraw.Draw(zoomed).line(
            [(z * (x // 2) + z // 2, 0), (z * (x // 2) + z // 2, z * y)],
            fill=ImageColor.getrgb("yellow"),
        )
        disp_img = ImageTk.PhotoImage(zoomed)
        self.roi_preview.img = disp_img  # type: ignore # protect from garbage collect
        self.roi_preview.configure(image=disp_img)
        self.update_crosscuts()

    def update_crosscuts(self):
        """Update cross cuts"""

        # delete drawings from last update
        self.cc_x.delete("all")
        self.cc_y.delete("all")

        # extract cross-cuts from full image (8 bit)
        roi_box = self.get_roi_box()
        x_cut = np.array(
            self.full_img.crop(
                (
                    roi_box[0],
                    self.full_img.size[1] // 2,
                    roi_box[2],
                    self.full_img.size[1] // 2 + 1,
                )
            )
        ).flatten()
        y_cut = np.array(
            self.full_img.crop(
                (
                    self.full_img.size[0] // 2,
                    roi_box[1],
                    self.full_img.size[0] // 2 + 1,
                    roi_box[3],
                )
            )
        ).flatten()

        # set size of cross-cuts to match roi image
        self.cc_x.configure(
            width=self.roi_preview.img.width(), height=200  # type: ignore
        )
        self.cc_y.configure(
            width=200, height=self.roi_preview.img.height()  # type: ignore
        )

        # NOTE: it seems Tk adds a 2-pixel all-around padding between the label border and the image,
        #       so this is to account for that so things line up with the cross-cuts.
        offset = 2
        bar_width_x = (self.roi_preview.img.width()) // len(x_cut)  # type: ignore
        bar_width_y = (self.roi_preview.img.height()) // len(y_cut)  # type: ignore

        for i in range(len(x_cut)):
            self.cc_x.create_rectangle(
                (
                    i * bar_width_x + offset,
                    0,
                ),
                (
                    (i + 1) * bar_width_x + offset,
                    self.cc_x.winfo_reqheight() * x_cut[i] / np.iinfo(x_cut.dtype).max,
                ),
                fill="gray",
            )
        for i in range(len(y_cut)):
            self.cc_y.create_rectangle(
                (
                    0,
                    i * bar_width_y + offset,
                ),
                (
                    self.cc_y.winfo_reqwidth() * y_cut[i] / np.iinfo(y_cut.dtype).max,
                    (i + 1) * bar_width_y + offset,
                ),
                fill="gray",
            )

        # guidelines
        self.cc_x.create_line(
            0,
            self.cc_x.winfo_reqheight() - 3,
            self.cc_x.winfo_reqwidth(),
            self.cc_x.winfo_reqheight() - 3,
            fill="red",
        )
        self.cc_y.create_line(
            self.cc_y.winfo_reqwidth() - 3,
            0,
            self.cc_y.winfo_reqwidth() - 3,
            self.cc_y.winfo_reqheight(),
            fill="red",
        )

    def update_img_props(self, camera_frame: Frame):
        """Update image properties"""
        prop_str = ""
        for p in [
            "bits",
            "rows",
            "cols",
            "bin",
            "gGain",
            "expTime",
            "frameTime",
            "timestamp",
            "triggered",
            "nTriggers",
            "freq",
        ]:
            prop_str += str(p) + ": " + str(getattr(camera_frame, p)) + "\n"
        self.img_props.set(prop_str.strip())

    def update_img_stats(self):
        """Update image statistics"""
        stats_txt = ""
        if self.camera_frame:
            image = self.camera_frame.img_array
        else:
            image = np.array(self.full_img)
        self.img_stats = get_centroid_and_variance(image)
        stats_txt += "Centroid: " + str(
            tuple(map(lambda v: round(v, 3), self.img_stats[0:2]))
        )
        stats_txt += "\nVariance: " + str(
            tuple(map(lambda v: round(v, 3), self.img_stats[2:]))
        )
        stats_txt += "\nStd Dev: " + str(
            tuple(map(lambda v: round(np.sqrt(v), 3), self.img_stats[2:4]))
        )
        stats_txt += "\nFWHM: " + str(
            tuple(map(lambda v: round(variance_to_fwhm(v), 3), self.img_stats[2:4]))
        )
        stats_txt += "\nMax Pixel Value: " + str(np.max(image))
        stats_txt += "\nSaturated Pixels: " + str(
            np.count_nonzero(image == np.iinfo(image.dtype).max)
        )
        self.img_stats_txt.set(stats_txt)

    def update_full_frame_preview(self):
        """Update the full frame preview"""
        # draw roi box
        roi_box = self.get_roi_box()
        img = self.full_img.convert("RGB")
        ImageDraw.Draw(img).rectangle(
            roi_box, width=3, outline=ImageColor.getrgb("yellow")
        )
        # draw FWHM
        c = self.img_stats
        x_hwhm = variance_to_fwhm(c[2]) / 2
        y_hwhm = variance_to_fwhm(c[3]) / 2
        ImageDraw.Draw(img).ellipse(
            (c[0] - x_hwhm, c[1] - y_hwhm, c[0] + x_hwhm, c[1] + y_hwhm),
            width=3,
            outline=ImageColor.getrgb("red"),
        )
        # display
        disp_img = ImageTk.PhotoImage(img.resize((img.width // 4, img.height // 4)))
        self.full_frame_preview.img = disp_img  # type: ignore # protect from garbage collect
        self.full_frame_preview.configure(image=disp_img)

    def update_histogram(self):
        """Draw histogram and labels"""
        # delete drawings from last update
        self.histogram.delete("all")

        # make text labels, reserve margin space for text
        margin_h = 30
        margin_v = 40
        self.histogram.create_text(
            self.histogram.winfo_reqwidth() / 2,
            0,
            anchor="n",
            text="Histogram of Pixel Values",
        )
        self.histogram.create_text(
            self.histogram.winfo_reqwidth() / 2,
            self.histogram.winfo_reqheight(),
            anchor="s",
            text="pixel value",
        )
        self.histogram.create_text(
            0,
            self.histogram.winfo_reqheight() / 2,
            angle=90,
            anchor="n",
            text="# of pixels",
        )

        # get histogram data
        if self.camera_frame:
            values, edges = np.histogram(
                self.camera_frame.img_array,
                range=(0, np.iinfo(self.camera_frame.img_array.dtype).max),
            )
        else:
            values, edges = np.histogram(
                np.array(self.full_img),
                range=(0, np.iinfo(np.array(self.full_img).dtype).max),
            )

        bar_width = (self.histogram.winfo_reqwidth() - 2 * margin_h) / len(values)

        for i in range(len(values)):
            self.histogram.create_rectangle(
                (
                    i * bar_width + margin_h,
                    self.histogram.winfo_reqheight() - margin_v,
                ),
                (
                    (i + 1) * bar_width + margin_h,
                    self.histogram.winfo_reqheight()
                    - margin_v
                    - (self.histogram.winfo_reqheight() - 2 * margin_v)
                    * values[i]
                    / max(values),
                ),
                fill="gray",
            )
            self.histogram.create_text(
                i * bar_width + margin_h,
                self.histogram.winfo_reqheight()
                - margin_v
                - (self.histogram.winfo_reqheight() - 2 * margin_v)
                * values[i]
                / max(values),
                anchor="nw",
                text=f"{values[i]}",
                font="TkDefaultFont 6",
                fill="white",
            )
            self.histogram.create_text(
                i * bar_width + margin_h,
                self.histogram.winfo_reqheight() - margin_v,
                anchor="n",
                text=edges[i],
                font="TkDefaultFont 6",
            )
        # last bar's end
        self.histogram.create_text(
            len(values) * bar_width + margin_h,
            self.histogram.winfo_reqheight() - margin_v,
            anchor="n",
            text=edges[-1],
            font="TkDefaultFont 6",
        )

    async def update_resolution(self):
        """Update resolution from camera, matching newest frame"""
        resolution: tuple[int, int] = (await self.camera.query_buffer())["resolution"]  # type: ignore
        self.camera_res_x.set(str(resolution[0]))
        self.camera_res_y.set(str(resolution[1]))
        self.update_resolution_flag = False

    async def update(self):
        """Update preview image in viewer"""
        if self.camera:
            # set camera info on first pass
            if self.extra_init:
                self.set_camera_info(await self.camera.get_camera_info())
                self.extra_init = False

            if self.freeze_txt.get() == "Freeze":  # means not frozen
                try:
                    self.camera_frame = self.camera.get_newest_frame()
                    self.full_img = Image.fromarray(self.camera_frame.display_array)
                    self.update_img_props(self.camera_frame)
                    if self.update_resolution_flag:
                        make_task(self.update_resolution(), self.tasks)
                except IndexError:
                    pass
        else:  # no camera, testing purposes
            if self.freeze_txt.get() == "Freeze":  # means not frozen
                # image components
                res = (int(self.camera_res_x.get()), int(self.camera_res_y.get()))
                black = Image.new(mode="L", size=res, color=0)
                # grey = Image.new(mode='L', size=res, color=20)
                noise = Image.effect_noise(size=res, sigma=50)
                gradient = ImageOps.invert(Image.radial_gradient(mode="L"))
                # set image to black and then paste in the gradient at specified position
                self.full_img = noise
                self.full_img.paste(gradient, (85, 400))

        self.update_img_stats()
        self.update_full_frame_preview()
        self.update_histogram()
        self.update_roi_img()

    def close(self):
        """Close out all tasks"""
        for t in self.tasks:
            t.cancel()
