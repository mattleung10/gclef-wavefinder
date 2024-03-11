import asyncio

from serial import Serial, SerialException, SerialTimeoutException

from ..gui.utils import Cyclic


class DkMonochromator(Cyclic):
    """Interface for Spectral Products DK series Monochromator"""

    READY = 0
    BUSY = 1
    ERROR = 2
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
        self.target_wavelength = 0.0
        self.current_wavelength = 0.0

        try:
            print(f"Connecting to monochromator on {port}... ", end="", flush=True)
            self.port.open()
        except (SerialException, ValueError) as e:
            self.status = DkMonochromator.ERROR
            self.port.close()
            print(e)
        else:
            # establish connection
            self.status = DkMonochromator.BUSY
            if self.ping():
                self.status = DkMonochromator.READY
                print("connected.")
            else:
                self.status = DkMonochromator.ERROR
                self.port.close()
                print("monochromater not found.")

    async def read_bytes(self, n: int = 1, timeout: float = 5) -> bytes:
        """Read n bytes, async"""
        timeout = max(timeout, 0.1)
        result = bytes()
        while n > 0:
            if timeout <= 0:
                raise SerialException("read timeout")
            b = self.port.read(n)
            if b:
                n -= len(b)
                result = result + b
            else:
                timeout -= 0.1
                await asyncio.sleep(0.1)
        return result

    async def read_status_end(self, timeout: float = 1):
        """Read status byte and cancel/end byte

        Raises SerialException if status is not zero or end byte is wrong
        """
        s = await self.read_bytes(2, timeout)
        # NOTE: Python yields an int when taking a slice of a bytes object...
        #       so work in ints for bitwise ops.
        if s[0] & int.from_bytes(b"\x80") == 0 and s[1] == 24:
            self.status = DkMonochromator.READY
        else:
            self.status = DkMonochromator.ERROR
            raise SerialException("bad data")

    def ping(self) -> bool:
        """Send ECHO command, look for reply

        Returns True if ping reply received
        """
        # do nothing if port is closed
        if not self.port.is_open:
            return False
        try:
            self.port.write(int(27).to_bytes())
            self.port.timeout = 5
            b = self.port.read(1)
            self.port.timeout = 0
            if b == int(27).to_bytes():
                return True
            else:
                raise SerialException("bad data")
        except (SerialException, SerialTimeoutException):
            return False

    async def get_sn(self) -> int:
        """Read serial number from monochromator"""
        sn = 0
        # do nothing if port is closed
        if not self.port.is_open:
            return sn
        # wait for ready
        while self.status != DkMonochromator.READY:
            await asyncio.sleep(0.1)
        self.status = DkMonochromator.BUSY
        # send command
        self.port.write(int(33).to_bytes())
        # read confirmation
        ack = await self.read_bytes()
        if ack != int(33).to_bytes():
            raise SerialException("bad data")
        # read 5 bytes and form the sn
        sn_bytes = await self.read_bytes(5)
        sn = int(sn_bytes.decode())
        # status & end bytes
        await self.read_status_end()
        return sn

    async def get_current_wavelength(self) -> float:
        """Get current wavelength in nm"""
        # do nothing if port is closed
        if not self.port.is_open:
            return self.current_wavelength
        # wait for ready
        while self.status != DkMonochromator.READY:
            await asyncio.sleep(0.1)
        self.status = DkMonochromator.BUSY
        # send command
        self.port.write(int(29).to_bytes())
        # read confirmation
        ack = await self.read_bytes()
        if ack != int(29).to_bytes():
            raise SerialException("bad data")
        # read 3 bytes and form the wavelength
        self.current_wavelength = float.fromhex((await self.read_bytes(3)).hex()) / 100
        # status & end bytes
        await self.read_status_end()
        return self.current_wavelength

    async def go_to_wavelength(self, wavelength):
        """Command monochromater to go to a wavelength

        Args:
            wavelength: in nanometers
        """
        # do nothing if port is closed
        if not self.port.is_open:
            return
        # wait for not-busy (error is ok)
        while self.status == DkMonochromator.BUSY:
            await asyncio.sleep(0.1)
        self.status = DkMonochromator.BUSY
        # send command
        self.port.write(int(16).to_bytes())
        # read confirmation
        ack = await self.read_bytes()
        if ack != int(16).to_bytes():
            raise SerialException("bad data")
        # convert wavelength to 3 bytes and send
        b = int(round(wavelength * 100)).to_bytes(3)
        self.port.write(b)
        # status & end bytes
        await self.read_status_end(timeout=30)

    async def step_up(self):
        """Move grating one step towards IR"""
        # do nothing if port is closed
        if not self.port.is_open:
            return
        # wait for not-busy (error is ok)
        while self.status == DkMonochromator.BUSY:
            await asyncio.sleep(0.1)
        self.status = DkMonochromator.BUSY
        # send command
        self.port.write(int(7).to_bytes())
        # read confirmation
        ack = await self.read_bytes()
        if ack != int(7).to_bytes():
            raise SerialException("bad data")
        # status & end bytes
        await self.read_status_end()

    async def step_down(self):
        """Move grating one step towards UV"""
        # do nothing if port is closed
        if not self.port.is_open:
            return
        # wait for not-busy (error is ok)
        while self.status == DkMonochromator.BUSY:
            await asyncio.sleep(0.1)
        self.status = DkMonochromator.BUSY
        # send command
        self.port.write(int(1).to_bytes())
        # read confirmation
        ack = await self.read_bytes()
        if ack != int(1).to_bytes():
            raise SerialException("bad data")
        # status & end bytes
        await self.read_status_end()

    async def update(self):
        try:
            # latch error until good command
            if self.status != DkMonochromator.ERROR:
                self.current_wavelength = await self.get_current_wavelength()
        except (SerialException, SerialTimeoutException) as e:
            self.status = DkMonochromator.ERROR

    def close(self):
        self.port.close()
