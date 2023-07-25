import asyncio
from gclib.gclib import GclibError, py

from .Axis import Axis


class GalilAxis(Axis):
    # Galil implementation of Axis superclass
    # See Axis for abstract function descriptions.

    def __init__(self, name: str, channel: str, connection: py,
                 accel: int = 2000000, decel: int = 2000000, speed: int = 100000) -> None:
        """Zaber motion control axis
        
        Args:
            name: human-readable name of axis
            channel: axis channel (A, B, C, D)
            connection: gclib py object with open connection
        """
        super().__init__(name)
        self.ch = channel
        self.g = connection
        self.accel = accel
        self.decel = decel
        self.speed = speed

        # enable axis with "Servo Here"
        s = self.g.GCommand(f"SH{self.ch}")
        # set acceleration, decleration, slew speed
        self.g.GCommand(f"AC{self.ch}=2000000")
        self.g.GCommand(f"DC{self.ch}=2000000")
        self.g.GCommand(f"SP{self.ch}=100000")
        self.g.GCommand(f"HV{self.ch}=5000")

    async def home(self):
        try:
            self.status = Axis.BUSY
            not_limit_reverse = bool(float(self.g.GCommand(f"MG _LR{self.ch}")))

            # jog negative until limit
            if not_limit_reverse:
                self.g.GCommand(f"JG{self.ch}=-{self.speed};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # Home
            self.g.GCommand(f"HM{self.ch};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # zero position
            self.g.GCommand(f"DE{self.ch}=0")
        except GclibError:
            self.status = Axis.ERROR

    async def move_relative(self, distance: float):
        # TODO counts per degree
        try:
            self.status = Axis.MOVING
            self.g.GCommand(f"PR{self.ch}={round(distance)};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
        except GclibError:
            self.status = Axis.ERROR
    
    async def move_absolute(self, distance: float):
        # TODO counts per degree
        try:
            self.status = Axis.MOVING
            self.g.GCommand(f"PA{self.ch}={round(distance)};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
        except GclibError:
            self.status = Axis.ERROR

    async def wait_for_motion_complete(self, ch: str):
        """Async wait for motion to be complete
        
        Args:
            ch: channel name of axis, e.g. "A"
        """
        while True:
            # MG _BG comes back as "0.0000"
            in_motion = bool(float(self.g.GCommand(f"MG _BG{ch}")))
            if in_motion > 0:
                await asyncio.sleep(0.1)
            else:
                return

    async def stop(self):
        try:
            self.g.GCommand("AB")
        except GclibError:
            self.status = Axis.ERROR
    
    async def update_position(self) -> float:
        s = self.g.GCommand(f"TP{self.ch}")
        self.position = float(s)
        return float(s)
    
    async def update_status(self) -> int:
        try:
            if self.status == Axis.ERROR:
                # latch errors until cleared by a good move
                self.status = Axis.ERROR
            else:
                tc1 = self.g.GCommand("TC1")
                code = tc1.split()[0]
                if int(code) > 0:
                    self.status = Axis.ERROR
                    # print error
                    print(f"Error on axis {self.name}: {tc1}")
                else:
                    # MG _BG comes back as "0.0000"
                    in_motion = bool(float(self.g.GCommand(f"MG _BG{self.ch}")))
                    if in_motion > 0:
                        self.status = Axis.BUSY
                    else:
                        self.status = Axis.READY
        except GclibError:
            self.status = Axis.ERROR
        return self.status
    
    async def set_limits(self, low_limit: float | None = None, high_limit: float | None = None):
        pass # TODO
    
    async def get_limits(self) -> tuple[float, float]:
        return (0., 0.) # TODO

    