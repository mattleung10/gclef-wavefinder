import usb.core

# Interface for Mightex Buffer USB Camera
# implemented from "Mightex Buffer USB Camera USB Protocol", v1.0.6.
class Camera:
    def __init__(self,res=(1280,1024),exposure_time=750,gain=4,fps=1000):
        print("Connecting to camera... ", end='')

        # find USB camera and set USB configuration
        self.dev = usb.core.find(idVendor=0x04b4, idProduct=0x0528)
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

    def reset(self):
        """Reset the camera; not recommended for normal use."""
        self.dev.write(0x01, [0x50, 1, 0x01])

    def read_reply(self):
        """Read reply from camera,
        check that it's good, and return data as a byte array.
        """
        reply = self.dev.read(0x81, 0xff)
        if not (reply[0] == 0x01 and len(reply[2:]) == reply[1]):
            raise RuntimeError("Bad Reply from Camera")
         # Strip out first two bytes (status & len)
        return reply[2:]

    def get_firmware_version(self):
        """Get camera firmware version as
        [Major, Minor, Revision].
        """
        self.dev.write(0x01, [0x01, 1, 0x01])
        return list(self.read_reply())

    def get_camera_info(self):
        """Get camera information."""

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
        info = dict()
        info["ConfigRv"] = int(reply[0])
        info["ModuleNo"] = reply[1:15].tobytes().decode()
        info["SerialNo"] = reply[15:29].tobytes().decode()
        info["MftrDate"] = reply[29:43].tobytes().decode()
        return info

    def print_introduction(self):
        """Print camera information."""
        for item in self.get_camera_info().items():
            print(item[0] + ": " + str(item[1]))
        print("Firmware: " + '.'.join(map(str, camera.get_firmware_version())))

    def set_mode(self, mode=0, bits=8):
        """Set camera work mode and bitrate.

        mode: 0 (default) for NORMAL; 1 for TRIGGER
        bits: 8 (default) or 12
        """
        self.work_mode = mode
        self.bits = bits
        self.dev.write(0x01, [0x30, 2, mode, bits])

    def set_frequency(self, freq_mode=0):
        """Set CCD frequency divider.

        freq = full / (2^freq_mode)
        0 = full speed; 1 = 1/2 speed; ... ; 4 = 1/16 speed
        """
        if freq_mode not in range(0,5):
            freq_mode = 0
        self.freq_mode = freq_mode
        self.dev.write(0x01, [0x32, 1, freq_mode])

    def set_configuration(self):
        """Write configuration to camera."""
        self.set_mode(self.work_mode, self.bits)
        self.set_frequency(self.freq_mode)


if __name__ == "__main__":
    camera = Camera()
    camera.print_introduction()
    camera.set_configuration()
    # img = camera.get_frame()
    # img.save("out.png","PNG")
