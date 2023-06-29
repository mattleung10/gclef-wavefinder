import tkinter as tk
from tkinter import ttk, filedialog

import numpy as np
from PIL import Image, ImageTk
from devices.MightexBufCmos import Camera

from zaber_motion.exceptions import ConnectionFailedException
from zaber_motion import Units
from zaber_motion.ascii import Connection

class App(tk.Tk):
    """Main graphical application"""

    def __init__(self):
        super().__init__()
        self.title("Detector Stage Control")
        self.grid()

        self.set_defaults()
        self.make_frames()
        self.create_devices()
        self.start_tasks()
        self.hydrate()

    def set_defaults(self):
        """Set application defaults"""
        self.view_delay = 1000 // 60 # 60 Hz
        self.def_padding = "3 3 12 12"
        self.check_resolution = False
        self.camera_info1 = tk.StringVar(self, value="")
        self.camera_info2 = tk.StringVar(self, value="")
        self.img_props = tk.StringVar(self, "")
        self.frame = None

        self.SN_X = 33938
        self.SN_Y = 33937
        self.SN_Z = 33939


    def make_frames(self):
        """Make view frames"""

        self.make_camera_control_frame()
        self.make_image_viewer_frame()

        # make motion control frame
        motion = ttk.Frame(self, padding=self.def_padding)
        motion.grid(column=0, row=1)
        
        self.pos_x = tk.StringVar(value="0")
        self.pos_y = tk.StringVar(value="0")
        self.pos_z = tk.StringVar(value="0")

        ttk.Label(motion, text="X").grid(column=0, row=0)
        ttk.Entry(motion, width=5, textvariable=self.pos_x,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=0, sticky=tk.E)
        ttk.Label(motion, text="Y").grid(column=0, row=1)
        ttk.Entry(motion, width=5, textvariable=self.pos_y,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=1, sticky=tk.E)
        ttk.Label(motion, text="Z").grid(column=0, row=2)
        ttk.Entry(motion, width=5, textvariable=self.pos_z,
            validatecommand=(self.register(self.valid_float), '%P'),
            # invalidcommand=self.register(self.restore_camera_entries), # TODO
            validate='focus').grid(column=1, row=2, sticky=tk.E)
        ttk.Button(motion, text="Go",
                   command=self.move_stages).grid(column=0, row=3)

    def make_image_viewer_frame(self):
        """Make image viewer frame"""
        viewer = ttk.LabelFrame(self, text="Preview",
                                labelanchor=tk.N, padding=self.def_padding)
        viewer.grid(column=1, row=0, sticky=tk.N)

        self.freeze_txt = tk.StringVar(value="Freeze")
        self.preview = ttk.Label(viewer)
        self.preview.grid(column=0, row=0, sticky=tk.N)
        props = ttk.Frame(viewer, padding=self.def_padding)
        props.grid(column=1, row=0, sticky=tk.N)
        ttk.Label(props, textvariable=self.img_props).grid(column=0, row=0, sticky=tk.W)
        ttk.Button(props, textvariable=self.freeze_txt,
                   command=self.freeze).grid(column=0, row=1, pady=10)
        ttk.Button(props, text="Save",
                   command=self.save_img).grid(column=0, row=2, sticky=tk.S)
    
    def make_camera_control_frame(self):
        """Make camera control frame"""

        cam_ctrl = ttk.LabelFrame(self, text="Camera Control",
                                  labelanchor=tk.N, padding=self.def_padding)
        cam_ctrl.grid(column=0, row=0, sticky=tk.N)

        self.camera_run_mode = tk.IntVar(value=Camera.NORMAL)
        self.camera_bits = tk.IntVar(value=8)
        self.camera_resolution1 = tk.StringVar(value="1280")
        self.camera_resolution2 = tk.StringVar(value="960")
        self.camera_bin_mode = tk.IntVar(value=Camera.NO_BIN)
        self.camera_exp_t = tk.StringVar(value="50.0")
        self.camera_fps = tk.StringVar(value="10.0")
        self.camera_gain = tk.StringVar(value="15")
        self.camera_freq = tk.StringVar(value="32")

        # camera info
        ttk.Label(cam_ctrl, text="Model").grid(column=0, row=0, sticky=tk.E, padx=10)
        ttk.Label(cam_ctrl, textvariable=self.camera_info1).grid(column=1, row=0,
                                                                 columnspan=2, sticky=tk.W)
        ttk.Label(cam_ctrl, text="S/N").grid(column=0, row=1, sticky=tk.E, padx=10)
        ttk.Label(cam_ctrl, textvariable=self.camera_info2).grid(column=1, row=1,
                                                                 columnspan=2, sticky=tk.W)

        # camera mode
        ttk.Label(cam_ctrl, text="Mode").grid(column=0, row=2, sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="Stream", value=Camera.NORMAL,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=2, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="Trigger", value=Camera.TRIGGER,
                        variable=self.camera_run_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=2, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="8 bit", value=8,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl).grid(column=1, row=3, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="12 bit", value=12,
                        variable=self.camera_bits,
                        command=self.set_cam_ctrl, # TODO add 12-bit
                        state=tk.DISABLED).grid(column=2, row=3, sticky=tk.W)

        # resolution
        ttk.Label(cam_ctrl, text="Resolution").grid(column=0, row=4,
                                                    sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_resolution1,
                  validatecommand=(self.register(self.valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=4, sticky=tk.E)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_resolution2,
                  validatecommand=(self.register(self.valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=2, row=4, sticky=tk.W)

        # binning
        ttk.Label(cam_ctrl, text="Binning").grid(column=0, row=5,
                                                 sticky=tk.E, padx=10)
        ttk.Radiobutton(cam_ctrl, text="No Bin", value=Camera.NO_BIN,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=5,
                                                        columnspan=2,
                                                        sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:2", value=Camera.BIN1X2,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=6, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:3", value=Camera.BIN1X3,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=6, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4", value=Camera.BIN1X4,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=1, row=7, sticky=tk.W)
        ttk.Radiobutton(cam_ctrl, text="1:4 skip", value=Camera.SKIP,
                        variable=self.camera_bin_mode,
                        command=self.set_cam_ctrl).grid(column=2, row=7,
                                                        columnspan=2,
                                                        sticky=tk.W)

        # exposure time
        ttk.Label(cam_ctrl, text="Exp. Time (ms)").grid(column=0, row=8, sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_exp_t,
                  validatecommand=(self.register(self.valid_float), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=8, sticky=tk.W)

        # FPS
        ttk.Label(cam_ctrl, text="Frames/Sec").grid(column=0, row=9,
                                                        sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_fps,
                  validatecommand=(self.register(self.valid_float), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=9, sticky=tk.W)

        # gain
        ttk.Label(cam_ctrl, text="Gain [6-41]dB").grid(column=0, row=10,
                                                       sticky=tk.E, padx=10)
        ttk.Entry(cam_ctrl, width=5, textvariable=self.camera_gain,
                  validatecommand=(self.register(self.valid_int), '%P'),
                  invalidcommand=self.register(self.restore_camera_entries),
                  validate='focus').grid(column=1, row=10, sticky=tk.W)
        
        # frequency
        ttk.Label(cam_ctrl, text="Frequency (MHz)").grid(column=0, row=11,
                                                     sticky=tk.E, padx=10)
        ttk.Combobox(cam_ctrl, textvariable=self.camera_freq,
                     values=["32", "16", "8", "4", "2"], state="readonly",
                     width=4).grid(column=1, row=11, sticky=tk.W)

        # buttons
        ttk.Button(cam_ctrl, text="Take Image",
                   command=self.snap_img).grid(column=0, row=12, pady=(10, 0), padx=10)
        ttk.Button(cam_ctrl, text="Write to Camera",
                   command=self.set_cam_ctrl).grid(column=1, row=12, columnspan=2,
                                                   sticky=tk.E, pady=(10, 0), padx=10)

    def create_devices(self):
        """Create device handles"""
        try:
            self.camera = Camera()
        except ValueError as e:
            print(e)
            self.camera = None
        try:
            zaber_con = Connection.open_serial_port("/dev/ttyUSB0")
            zaber_con.enable_alerts()

            device_list = zaber_con.detect_devices()
            det_stage_x = next(filter(lambda d: d.serial_number == self.SN_X, device_list))
            det_stage_y = next(filter(lambda d: d.serial_number == self.SN_Y, device_list))
            det_stage_z = next(filter(lambda d: d.serial_number == self.SN_Z, device_list))

            self.det_ax = det_stage_x.get_axis(1)
            self.det_ay = det_stage_y.get_axis(1)
            self.det_az = det_stage_z.get_axis(1)
        except ConnectionFailedException as e:
            print(e)
            self.det_ax = None
            self.det_ay = None
            self.det_az = None

    def start_tasks(self):
        """Start cyclic tasks."""
        self.preview.after(self.view_delay, self.update_preview)

    def hydrate(self):
        """Fill in UI elements"""
        if self.camera:
            info = self.camera.get_camera_info()
            self.camera_info1.set(info["ModuleNo"].strip('\0')) # type: ignore
            self.camera_info2.set(info["SerialNo"].strip('\0')) # type: ignore

    def update_preview(self):
        """Update preview image in viewer"""

        if self.camera:
            self.camera.acquire_frames()
            if self.freeze_txt.get() == "Freeze":
                self.frame = self.camera.get_newest_frame()
                if self.frame:
                    self.frame_img = Image.fromarray(self.frame.img)
                    # frame_img = Image.fromarray(np.random.randint(255, size=(960, 1280), dtype=np.uint8)) # random noise
                    disp_img = ImageTk.PhotoImage(self.frame_img.resize((self.frame_img.width // 4,
                                                                         self.frame_img.height // 4)))
                    self.preview.img = disp_img # type: ignore # protect from garbage collect
                    self.preview.configure(image=disp_img)

                    # update img_props
                    prop_str = self.img_props.get()
                    prop_str = ""
                    for p in ["rows", "cols", "bin", "gGain", "expTime", "frameTime",
                            "timestamp", "triggered", "nTriggers", "freq"]:
                        prop_str += str(p) + ': ' + str(getattr(self.frame, p)) + '\n'
                    self.img_props.set(prop_str.strip())

                    # update UI to proper values, matching newest frame
                    if self.check_resolution:
                        resolution : tuple[int,int] = self.camera.query_buffer()["resolution"] # type: ignore
                        self.camera_resolution1.set(str(resolution[0]))
                        self.camera_resolution2.set(str(resolution[1]))
                        self.check_resolution = False

        self.preview.after(self.view_delay, self.update_preview)

    def set_cam_ctrl(self):
        """Set camera to new settings"""
        if self.camera:
            self.camera.set_mode(run_mode=self.camera_run_mode.get(),
                                 # TODO bits=self.camera_bits.get()
                                 write_now=True)
            resolution = ((int(self.camera_resolution1.get()),
                           int(self.camera_resolution2.get())))
            self.camera.set_resolution(resolution=resolution,
                                       bin_mode=self.camera_bin_mode.get(),
                                       write_now=True)
            self.camera.set_exposure_time(exposure_time=float(self.camera_exp_t.get()),
                                          write_now=True)
            self.camera.set_fps(fps=float(self.camera_fps.get()),
                                write_now=True)
            self.camera.set_gain(gain=int(self.camera_gain.get()),
                                 write_now=True)
            freq_div = (int.bit_length(32 // int(self.camera_freq.get())) - 1)
            self.camera.set_frequency(freq_mode=freq_div, write_now=True)

            # read back validated settings from camera
            self.restore_camera_entries()

    def restore_camera_entries(self):
        """Restore camera entry boxes from camera"""
        if self.camera:
            # throw out old frames
            self.camera.clear_buffer()
            # tell update_preview to also update the resolution
            self.check_resolution = True
            # put back entries
            self.camera_exp_t.set(str(self.camera.exposure_time))
            self.camera_fps.set(str(self.camera.fps))
            self.camera_gain.set(str(self.camera.gain))
            self.camera_freq.set(str((32 >> self.camera.freq_mode)))

    def snap_img(self):
        """Snap and image"""
        if self.camera:
            self.camera.trigger()

    def save_img(self):
        """Save image dialog"""
        # TODO: FITS format
        if self.frame:
            f = filedialog.asksaveasfilename(initialdir="images/",
                                             initialfile="img.png",
                                             filetypes = (("image files",["*.jpg","*.png"]),
                                                          ("all files","*.*")),
                                             defaultextension=".png")
            if f:
                self.frame_img.save(f)

    def freeze(self):
        """Freeze preview"""
        if self.freeze_txt.get() == "Freeze":
            self.freeze_txt.set("Unfreeze")
        else:
            self.freeze_txt.set("Freeze")

    def move_stages(self):
        """Move Zaber stages"""
        if self.det_ax:
            self.det_ax.move_absolute(float(self.pos_x.get()), Units.LENGTH_MILLIMETRES)
        if self.det_ay:
            self.det_ay.move_absolute(float(self.pos_y.get()), Units.LENGTH_MILLIMETRES)
        if self.det_az:
            self.det_az.move_absolute(float(self.pos_z.get()), Units.LENGTH_MILLIMETRES)

    def valid_int(self, i_str : str):
        """Check if a int value is valid"""
        try:
            float(i_str)
        except:
            return False
        else:
            return True

    def valid_float(self, f_str : str):
        """Check if a float value is valid"""
        try:
            float(f_str)
        except:
            return False
        else:
            return True


if __name__ == "__main__":
    app = App()
    app.mainloop()