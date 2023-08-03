import array
import asyncio
import os
import platform

import numpy as np
import usb.core

from ..gui.utils import Cyclic


class Frame:
    """Image frame object for Mightex camera"""

    def __init__(self, frame: array.array) -> None:
        # store properties (little endian format)
        frame_prop = frame[-512:] # last 512 bytes
        self.rows       = frame_prop[0]  + (frame_prop[1]  << 0x8) # number of rows
        self.cols       = frame_prop[2]  + (frame_prop[3]  << 0x8) # number of columns
        self.bin        = frame_prop[4]  + (frame_prop[5]  << 0x8) # bin mode
        self.xStart     = frame_prop[6]  + (frame_prop[7]  << 0x8) # always 0
        self.yStart     = frame_prop[8]  + (frame_prop[9]  << 0x8) # ROI column start
        self.rGain      = frame_prop[10] + (frame_prop[11] << 0x8) # red gain
        self.gGain      = frame_prop[12] + (frame_prop[13] << 0x8) # green/monochrome gain
        self.bGain      = frame_prop[14] + (frame_prop[15] << 0x8) # blue gain
        self.timestamp  = frame_prop[16] + (frame_prop[17] << 0x8) # timestamp in ms
        self.triggered  = frame_prop[18] + (frame_prop[19] << 0x8) # true if triggered
        self.nTriggers  = frame_prop[20] + (frame_prop[21] << 0x8) # number of trigger events \
                                                                   # since trigger mode was set
        # reserved property "UserMark" in this space
        self.frameTime  = frame_prop[24] + (frame_prop[25] << 0x8) # frame time relates \
                                                                   # to frames per second
        self.freq       = frame_prop[26] + (frame_prop[27] << 0x8) # CCD frequency mode
        self.expTime    = 0.05 * ((frame_prop[28] << 0x00) +       # exposure time in ms
                                  (frame_prop[29] << 0x08) +
                                  (frame_prop[30] << 0x16) +
                                  (frame_prop[31] << 0x24))
        # last 480 bytes are reserved, not used

        # TODO: support 12-bit

        if (len(frame) != self.rows*self.cols + 512):
            raise BufferError("got bad frame from camera")
        # store image; for some reason the rows and cols are switched in the buffer
        self.img = np.reshape(frame[0 : self.rows*self.cols], (self.cols, self.rows))

class Camera(Cyclic):
    """Interface for Mightex Buffer USB CMOS Camera

    Implemented from "Mightex Buffer USB Camera USB Protocol", v1.0.6;
    Defaults are for camera model CGN-B013-U

    Not implemented: on-chip ROI, GPIO
    """

    # run modes; see function set_mode for description
    NORMAL  = 0
    TRIGGER = 1
    RUN_MODES = [NORMAL, TRIGGER]
    # bin modes; see function set_resolution for description
    NO_BIN = 0
    BIN1X2 = 0x81
    BIN1X3 = 0x82
    BIN1X4 = 0x83
    SKIP   = 0x03
    BIN_MODES = [NO_BIN, BIN1X2, BIN1X3, BIN1X4, SKIP]

    def __init__(self,
                 run_mode: int = NORMAL,
                 bits: int = 8,
                 freq_mode: int = 0,
                 resolution: tuple[int, int] = (1280, 960),
                 bin_mode: int = NO_BIN,
                 nBuffer: int = 24,
                 exposure_time: float = 50,
                 fps: float = 10,
                 gain: int = 15) -> None:
        """Mightex Buffer USB CMOS Camera

        Args:
            run_mode: NORMAL (streaming video) or TRIGGER (single exposure)
            bits: 8 or 12
            freq_mode: frequency divider, see function set_frequency
            resolution: tuple[rows, columns]
            bin_mode: binning mode, see function set_resolution
            nBuffer: size of camera buffer, defaults to maximum of 24
            exposure_time: exposure time in milliseconds, in increments of 0.05ms
            fps: NORMAL mode target frames per second
            gain: 6 to 41 dB, inclusive, see function set_gain
        """

        # flag to run extra initialization on first async loop
        self.extra_init = True

        # camera configuration
        self.run_mode = run_mode
        self.bits = bits
        self.freq_mode = freq_mode
        self.resolution = resolution
        self.bin_mode = bin_mode
        self.nBuffer = nBuffer
        self.exposure_time = exposure_time
        self.fps = fps
        self.gain = gain

        # data structures
        self.app_buffer: list[Frame] = []
        self.buffer_max = 100 # max 100 frames

        print("Connecting to Mightex camera... ", end='', flush=True)

        # For Windows, load in the included libusb-1.0.dll by adding it to the PATH,
        # where pyusb will find it.
        if "Windows".casefold() in platform.platform().casefold():
            libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "lib"))
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + libpath

        # find USB camera and set USB configuration
        self.dev: usb.core.Device = usb.core.find(idVendor=0x04b4,
                                                  idProduct=0x0528) # type: ignore
        if self.dev is None:
            raise ValueError("not found.")
        self.dev.set_configuration() # type: ignore

        self.establish_connection()
        print("connected.")

    def establish_connection(self):
        """Write to and read from the camera until connection is established
        
        Not async, will block.
        """
        while True:
            try:
                self.dev.write(0x01, [0x01, 1, 0x01])
                self.dev.read(0x81, 0xff)
                break
            except usb.core.USBTimeoutError:
                continue

    async def reset(self) -> None:
        """Reset the camera; not recommended for normal use."""
        self.dev.write(0x01, [0x50, 1, 0x01])

    async def read_reply(self) -> array.array:
        """Read reply from camera, check that it's good,
        and return data as an array.

        The first byte is supposed to return 0x01 for "ok,"
        but the 0x33 command returns 0x08 for "ok,"
        so we're just checking for non-zero replies.
        """
        reply = self.dev.read(0x81, 0xff)
        if not (reply[0] > 0x00 and len(reply[2:]) == reply[1]):
            raise RuntimeError("Bad Reply from Camera:\n" + str(reply))
        # Strip out first two bytes (status & len)
        return reply[2:]

    async def get_firmware_version(self) -> list[int]:
        """Get camera firmware version as
        [Major, Minor, Revision].
        """
        self.dev.write(0x01, [0x01, 1, 0x01])
        return list(await self.read_reply())

    async def get_camera_info(self) -> dict[str, str | int]:
        """Get camera information.

        returns a dict with keys "ConfigRev", "ModuleNo", "SerialNo", "MftrDate"
        """
        self.dev.write(0x01, [0x21, 1, 0x00])
        reply = await self.read_reply()
        info: dict[str, str | int] = {}
        info["ConfigRv"] = int(reply[0])                    # configuration version
        info["ModuleNo"] = reply[1:15].tobytes().decode()   # camera model
        info["SerialNo"] = reply[15:29].tobytes().decode()  # serial number
        info["MftrDate"] = reply[29:43].tobytes().decode()  # manufacture date (not set)
        return info

    async def print_introduction(self) -> None:
        """Print camera information."""
        for item in (await self.get_camera_info()).items():
            print(item[0] + ": " + str(item[1]))
        print("Firmware: " + '.'.join(map(str, await self.get_firmware_version())))

    async def set_mode(self, run_mode: int = NORMAL,
                       bits: int = 8, write_now: bool = False) -> None:
        """Set camera work mode and bitrate.

        run_mode:   NORMAL (default) or TRIGGER
        bits:       8 (default) or 12
        write_now:  write to camera immediately
        """
        self.run_mode = run_mode if run_mode in Camera.RUN_MODES else Camera.NORMAL
        self.bits = bits if bits in [8, 12] else 8
        if write_now:
            self.dev.write(0x01, [0x30, 2, self.run_mode, self.bits])

    async def set_frequency(self, freq_mode: int = 0, write_now: bool = False) -> None:
        """Set CCD frequency divider.

        freq_mode: frequency divider; freq = full / (2^freq_mode)
        write_now: write to camera immediately

        0 = full speed; 1 = 1/2 speed; ... ; 4 = 1/16 speed
        """
        self.freq_mode = freq_mode if freq_mode in range(0,5) else 0
        if write_now:
            self.dev.write(0x01, [0x32, 1, self.freq_mode])

    async def set_resolution(self, resolution: tuple[int, int] = (1280, 960),
                             bin_mode: int = NO_BIN, nBuffer: int = 24,
                             write_now: bool = False) -> None:
        """Set camera resolution, bin mode, and buffer size.

        resolution: tuple of (rows, columns)
        bin_mode:   binning mode; see below.
        nBuffer:    size of camera buffer, defaults to maximum of 24
        write_now:  write to camera immediately

        NO_BIN = 0      # full resolution (1280 x 480)
        BIN1X2 = 0x81   # 1:2 Bin mode, it's pre-defined as: 1280 x 480
        BIN1X3 = 0x82   # 1:3 Bin mode, it's pre-defined as: 1280 x 320
        BIN1X4 = 0x83   # 1:4 Bin mode, it's pre-defined as: 1280 x 240
        SKIP   = 0x03   # 1:4 Bin mode2, it's pre-defined as: 1280 x 240
        """
        self.resolution = tuple(np.clip(resolution, 8, 1280))
        self.bin_mode   = bin_mode if bin_mode in Camera.BIN_MODES else Camera.NO_BIN
        self.nBuffer    = np.clip(nBuffer, 1, 24)
        if write_now:
            # last parameter "buffer option" should always be zero
            self.dev.write(0x01, [0x60, 7,
                                  self.resolution[0] >> 8, self.resolution[0] & 0xff,
                                  self.resolution[1] >> 8, self.resolution[1] & 0xff,
                                  self.bin_mode, self.nBuffer, 0])

    async def set_exposure_time(self, exposure_time: float = 50,
                                write_now: bool = False) -> None:
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

    async def set_fps(self, fps: float = 10, write_now: bool = False) -> None:
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

    async def set_gain(self, gain: int = 15, write_now: bool = False) -> None:
        """Set camera gain.

        gain:       6 to 41 dB, inclusive
        write_now:  write to camera immediately

        In most of the applications, the Minimum Gain
        recommended for CGX-B013-U/CGX-C013-U is as following:
        - No Bin mode ( Bin = 0),
                Gain = 15 (dB) for B013 module and 17(dB) for C013 module.
        - 1:2 Bin mode ( Bin = 0x81), Gain = 8 (dB)
        - 1:3 Bin mode ( Bin = 0x82), Gain = 6 (dB)
        - 1:4 Bin mode ( Bin = 0x83), Gain = 6 (dB)
        """
        self.gain = np.clip(gain, 6, 41)
        if write_now:
            self.dev.write(0x01, [0x62, 3, self.gain, self.gain, self.gain])

    async def write_configuration(self) -> None:
        """Write all configuration settings to camera."""
        await self.set_mode(self.run_mode, self.bits, write_now=True)
        await self.set_frequency(self.freq_mode, write_now=True)
        await self.set_resolution(self.resolution, self.bin_mode, self.nBuffer, write_now=True)
        await self.set_exposure_time(self.exposure_time, write_now=True)
        await self.set_fps(self.fps, write_now=True)
        await self.set_gain(self.gain, write_now=True)

    async def trigger(self) -> None:
        """Simulate a trigger.

        Only works in TRIGGER mode.
        """
        self.dev.write(0x01, [0x36, 1, 0x00])

    async def query_buffer(self) -> dict[str, int | tuple[int, int]]:
        """Query camera's buffer for number of available frames
        and configuration.

        returns dict with keys "nFrames", "resolution", "bin_mode"
        """
        self.dev.write(0x01, [0x33, 1, 0x00])
        reply = await self.read_reply()
        buffer_info: dict[str, int | tuple[int, int]] = {}
        buffer_info["nFrames"] = reply[0]
        buffer_info["resolution"] = ((reply[1] << 8) + reply[2],
                                     (reply[3] << 8) + reply[4])
        buffer_info["bin_mode"] = reply[5]
        return buffer_info

    async def clear_buffer(self, fut=None) -> None:
        """Clear camera and application buffer."""
        nFrames = (await self.query_buffer())["nFrames"]
        self.dev.write(0x01, [0x35, 1, nFrames])
        self.app_buffer.clear()

    async def acquire_frames(self) -> None:
        """Aquire camera image frames.

        Downloads all available frames from the camera buffer and puts them
        in the application buffer.
        """
        while True:
            # get frame buffer information
            buffer_info = await self.query_buffer()
            nFrames: int = buffer_info["nFrames"] # type: ignore
            resolution: tuple[int, int] = buffer_info["resolution"] # type: ignore

            # check camera buffer size
            if nFrames == 0:
                break
            elif nFrames == self.nBuffer:
                print("camera buffer full")

            # tell camera to send one frame
            self.dev.write(0x01, [0x34, 1, 1])

            # determine frame data size, padded to 512 byte alignment
            nPixels = resolution[0] * resolution[1]
            bytes_per_px = 1 if self.bits == 8 else 2
            padding = (bytes_per_px * nPixels) % 512
            # the last 512 bytes are the frame properties
            frame_size = nPixels * bytes_per_px + padding + 512

            # read one frame and insert into app buffer
            try:
                data = self.dev.read(0x82, frame_size)
            except usb.core.USBTimeoutError:
                break
            try:
                frame = Frame(data)
            except BufferError:
                break
            self.app_buffer.insert(0, frame)
            # trim buffer
            while len(self.app_buffer) > self.buffer_max:
                self.app_buffer.pop()

    def get_frames(self, nFrames: int = 1) -> list[Frame]:
        """Get most recent nFrames frames, from newest to oldest"""
        nFrames = np.clip(nFrames, 0, len(self.app_buffer))
        return self.app_buffer[0:nFrames]

    def get_newest_frame(self) -> Frame:
        """Get most recent frame."""
        if len(self.app_buffer) > 0:
            return self.app_buffer[0]
        else:
            raise IndexError("no frames in app buffer")

    async def update(self):
        """Update application with new data from camera"""
        if self.extra_init:
            print("Writing configuration to camera... ", end='', flush=True)
            await self.write_configuration()
            print("OK.")
            self.extra_init = False
        await self.acquire_frames()

    def close(self):
        """Close connection to camera
        
        Don't need to do anything.
        """
        pass