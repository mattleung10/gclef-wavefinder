import time
import array
from queue import Queue

import numpy as np
import usb.core


class Camera:
    """Interface for Mightex Buffer USB Camera.

    Implemented from "Mightex Buffer USB Camera USB Protocol", v1.0.6;
    Defaults are for camera model CGN-B013-U
    """

    # run modes; see function set_mode for description
    NORMAL  = 0
    TRIGGER = 1
    # bin modes; see function set_resolution for description
    NO_BIN = 0
    BIN1X2 = 0x81
    BIN1X3 = 0x82
    BIN1X4 = 0x83
    SKIP   = 0x03
    BIN_MODES = [NO_BIN, BIN1X2, BIN1X3, BIN1X4, SKIP]

    def __init__(self,
                 run_mode : int = NORMAL,
                 bits : int = 8,
                 freq_mode : int = 0,
                 resolution : tuple[int, int] =(1280,960),
                 bin_mode : int = NO_BIN,
                 nbuffer : int = 24,
                 exposure_time : float = 50,
                 fps : float = 10,
                 gain : int = 15) -> None:
        
        # set configuration
        self.run_mode = run_mode
        self.bits = bits
        self.freq_mode = freq_mode
        self.resolution = resolution
        self.bin_mode = bin_mode
        self.nbuffer = nbuffer
        self.exposure_time = exposure_time
        self.fps = fps
        self.gain = gain

        # data structures
        self.frame_buffer : Queue[Frame] = Queue(100) # max 100 frames

        print("Connecting to camera... ", end='')

        # find USB camera and set USB configuration
        self.dev : usb.core.Device = usb.core.find(idVendor=0x04b4, idProduct=0x0528)
        if self.dev is None:
            raise ValueError("Mightex camera not found")
        self.dev.set_configuration()
        
        # get firmware version until connection works
        while True:
            try:
                self.get_firmware_version()
                break
            except usb.core.USBTimeoutError:
                continue
        print("connected!")

        # write config to camera
        print("Writing configuration to camera... ", end='')
        self.write_configuration()
        print("success!")

    def reset(self) -> None:
        """Reset the camera; not recommended for normal use."""
        self.dev.write(0x01, [0x50, 1, 0x01])

    def read_reply(self) -> array.array:
        """Read reply from camera,
        check that it's good, and return data as an array.
        """
        reply = self.dev.read(0x81, 0xff)
        if not (reply[0] > 0x00 and len(reply[2:]) == reply[1]):
            raise RuntimeError("Bad Reply from Camera:\n" + str(reply))
        # Strip out first two bytes (status & len)
        return reply[2:]

    def get_firmware_version(self) -> list[int]:
        """Get camera firmware version as
        [Major, Minor, Revision].
        """
        self.dev.write(0x01, [0x01, 1, 0x01])
        return list(self.read_reply())

    def get_camera_info(self) -> dict[str, str | int]:
        """Get camera information.
        
        returns a dict with keys "ConfigRev", "ModuleNo", "SerialNo", "MftrDate"
        """

        # #define STRING_LENGTH 14
        # typedef struct
        # {
        #   BYTE ConfigRevision;
        #   BYTE ModuleNo[STRING_LENGTH];
        #   BYTE SerialNo[STRING_LENGTH];
        #   BYTE ManuafactureDate[STRING_LENGTH];
        # } tDeviceInfo;
        self.dev.write(0x01, [0x21, 1, 0x00])
        reply = self.read_reply()
        info : dict[str, str | int] = dict()
        info["ConfigRv"] = int(reply[0])
        info["ModuleNo"] = reply[1:15].tobytes().decode()
        info["SerialNo"] = reply[15:29].tobytes().decode()
        info["MftrDate"] = reply[29:43].tobytes().decode()
        return info

    def print_introduction(self) -> None:
        """Print camera information."""
        for item in self.get_camera_info().items():
            print(item[0] + ": " + str(item[1]))
        print("Firmware: " + '.'.join(map(str, camera.get_firmware_version())))

    def set_mode(self, run_mode : int = NORMAL, bits : int = 8, write_now : bool = False) -> None:
        """Set camera work mode and bitrate.

        run_mode:   NORMAL (default) or TRIGGER
        bits:       8 (default) or 12
        write_now:  write to camera immediately
        """
        self.run_mode = run_mode if run_mode in [Camera.NORMAL, Camera.TRIGGER] else Camera.NORMAL
        self.bits = bits if bits in [8, 12] else 8
        if write_now:
            self.dev.write(0x01, [0x30, 2, self.run_mode, self.bits])

    def set_frequency(self, freq_mode : int = 0, write_now : bool = False) -> None:
        """Set CCD frequency divider.

        freq_mode: frequency divider; freq = full / (2^freq_mode)
        write_now: write to camera immediately

        0 = full speed; 1 = 1/2 speed; ... ; 4 = 1/16 speed
        """
        self.freq_mode = freq_mode if freq_mode in range(0,5) else 0
        if write_now:
            self.dev.write(0x01, [0x32, 1, self.freq_mode])

    def set_resolution(self, resolution : tuple[int, int] = (1280, 960),
                       bin_mode : int = NO_BIN, nbuffer : int = 24, write_now : bool = False):
        """Set camera resolution, bin mode, and buffer size.
        
        resolution: tuple of (rows, columns)
        bin_mode:   binning mode; see below.
        nbuffer:    size of camera buffer, defaults to maximum of 24
        write_now:  write to camera immediately

        NO_BIN = 0      # full resolution (1280 x 480)
        BIN1X2 = 0x81   # 1:2 Bin mode, it's pre-defined as: 1280 x 480
        BIN1X3 = 0x82   # 1:3 Bin mode, it's pre-defined as: 1280 x 320
        BIN1X4 = 0x83   # 1:4 Bin mode, it's pre-defined as: 1280 x 240
        SKIP   = 0x03   # 1:4 Bin mode2, it's pre-defined as: 1280 x 240
        """
        self.resolution = tuple(np.clip(resolution, 1, 1280))
        self.bin_mode   = bin_mode if bin_mode in Camera.BIN_MODES else Camera.NO_BIN
        self.nbuffer    = np.clip(nbuffer, 1, 24)
        if write_now:
            # last parameter "buffer option" should always be zero
            self.dev.write(0x01, [0x60, 7,
                                  self.resolution[0] >> 8, self.resolution[0] & 0xff,
                                  self.resolution[1] >> 8, self.resolution[1] & 0xff,
                                  self.bin_mode, self.nbuffer, 0])

    def set_exposure_time(self, exposure_time : float = 50, write_now : bool = False):
        """Set exposure time.

        exposure_time:  time in milliseconds, in increments of 0.05ms
        write_now:      write to camera immediately

        maximum exposure time is 200s
        """
        self.exposure_time = np.clip(exposure_time, 0.05, 200000)
        if write_now:
            set_val = int(self.exposure_time / 0.05)
            self.dev.write(0x01, [0x63, 4,
                                  (set_val >> 24),
                                  (set_val >> 16) & 0xff,
                                  (set_val >>  8) & 0xff,
                                  (set_val >>  0) & 0xff])

    def set_fps(self, fps : float = 10, write_now : bool = False):
        """Set frames per second.

        fps:        frames per second
        write_now:  write to camera immediately

        units are 0.1ms per frame
        maximum fps is 10000 (0.1ms frame time) 
        mimumum fps is 10000/65535 ~= 0.153
        """
        self.fps = np.clip(fps, 0.153, 10000)
        if write_now:
            frame_time = 1/self.fps
            set_val = int(frame_time * 10000)
            self.dev.write(0x01, [0x64, 2, set_val >> 8, set_val & 0xff])

    def set_gain(self, gain : int = 15, write_now : bool = False):
        """Set camera gain.
        
        gain:       6 to 41 db, inclusive
        write_now:  write to camera immediately

        In most of the applications, the Minimum Gain
        recommended for CGX-B013-U/CGX-C013-U is as following:
        - No Bin mode ( Bin = 0) , Gain = 15 (dB) for B013 module and 17(dB) for C013 module.
        - 1:2 Bin mode ( Bin = 0x81), Gain = 8 (dB)
        - 1:3 Bin mode ( Bin = 0x82), Gain = 6 (dB)
        - 1:4 Bin mode ( Bin = 0x83), Gain = 6 (dB)
        """
        self.gain = np.clip(gain, 6, 41)
        if write_now:
            self.dev.write(0x01, [0x62, 3, self.gain, self.gain, self.gain])

    def trigger(self):
        """Simulate a trigger.
        
        Only works in TRIGGER mode.
        """
        self.dev.write(0x01, [0x36, 1, 0x00])

    def query_buffer(self):
        """Query camera's buffer for number of available frames and configuration.
        
        returns dict with keys "nframes", "resolution", "bin_mode"
        """
        self.dev.write(0x01, [0x33, 1, 0x00])
        reply = self.read_reply()
        buffer_info = dict()
        buffer_info["nframes"] = reply[0]
        buffer_info["resolution"] = ((reply[1] << 8) + reply[2],
                                     (reply[3] << 8) + reply[4])
        buffer_info["bin_mode"] = reply[5]
        return buffer_info

    def clear_buffer(self) -> None:
        """Clear camera buffer."""
        self.dev.write(0x01, [0x33, 1, 0x00])
        frame_count = self.read_reply()[0]
        self.dev.write(0x01, [0x35, 1, frame_count])

    def get_images(self):
        """Get camera image frames (data) from buffer."""
        pass

    def write_configuration(self):
        """Write all configuration settings to camera."""
        self.set_mode(self.run_mode, self.bits, write_now=True)
        self.set_frequency(self.freq_mode, write_now=True)
        self.set_resolution(self.resolution, self.bin_mode, self.nbuffer, write_now=True)
        self.set_exposure_time(self.exposure_time, write_now=True)
        self.set_fps(self.fps, write_now=True)
        self.set_gain(self.gain, write_now=True)

class Frame:
    """Image frame object."""

    def __init__(self) -> None:
        pass



if __name__ == "__main__":
    camera = Camera()
    camera.print_introduction()
    while True:
        time.sleep(0.1)
        print(camera.query_buffer())
    # img = camera.get_frame()
    # img.save("out.png","PNG")
