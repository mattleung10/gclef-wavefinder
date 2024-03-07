import asyncio

from serial import Serial, SerialException, SerialTimeoutException

from ..gui.utils import Cyclic


class DkMonochromator(Cyclic):
    """Interface for Spectral Products DK series Monochromator"""

    READY = 0
    BUSY = 2
    ERROR = 3
    STATES = [READY, BUSY, ERROR]

    def __init__(self, port: str) -> None:
        self.port = Serial(
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=0,  # non-blocking mode
                rtscts=True,
                write_timeout=1.0,
                dsrdtr=True,
            )
        self.port.port = port
        self.status = DkMonochromator.BUSY
        try:
            print(f"Connecting to monochromator on {port}... ", end="", flush=True)
            self.port.open()
        except (SerialException, ValueError) as e:
            self.status = DkMonochromator.ERROR
            self.port.close()
            print(e)
        else:
            # establish connection
            if self.ping():
                self.status = DkMonochromator.READY
                print("connected.")
            else:
                self.status = DkMonochromator.ERROR
                self.port.close()
                print("monochromater not found.")

    async def read_bytes(self, n: int = 1) -> bytes:
        """Read n bytes, async"""
        result = bytes()
        while n > 0:
            b = self.port.read(n)
            if b:
                n -= 1
                result = result + b
            else:
                await asyncio.sleep(0.1)
        return result

    async def read_status_end(self):
        """Read status byte and cancel/end byte"""
        s = await self.read_bytes(2)
        await self.read_bytes()
        self.status = DkMonochromator.READY if s[0] == 0 else DkMonochromator.ERROR

    def ping(self) -> bool:
        """Send ECHO command, look for reply

        Temporarily modifies port's timeout. Does not update status.

        Returns True if ping reply received
        """
        try:
            old_timeout = self.port.timeout
            self.port.timeout = 1.0
            self.port.write(b"\x27")
            b = self.port.read()
            self.port.timeout = old_timeout
            if b == b"\x27":
                return True
            else:
                raise SerialException
        except (SerialException, SerialTimeoutException):
            return False

    async def read_sn(self) -> int:
        """Read serial number from monochromator"""
        sn = 0
        if self.status == DkMonochromator.READY:
            self.status = DkMonochromator.BUSY
            # send command
            self.port.write(b"\x33")
            # read 5 bytes and form the sn
            sn_bytes = await self.read_bytes(5)
            for b in sn_bytes:
                sn = 10 * sn + int(b)
            # status & end bytes
            await self.read_status_end()
        return sn

    async def update(self):
        pass
        # TODO: read current wavelength

    def close(self):
        self.port.close()
