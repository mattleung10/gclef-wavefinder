from gclib.gclib import GclibError, py

from .Axis import Axis


class GalilAxis(Axis):
    # Galil implementation of Axis superclass
    # See Axis for abstract function descriptions.

    def __init__(self, name: str, channel: str, connection: py) -> None:
        """Zaber motion control axis
        
        Args:
            name: human-readable name of axis
            channel: axis channel (A, B, C, D)
            connection: gclib py object with open connection
        """
        super().__init__(name)
        self.ch = channel
        self.g = connection

        # enable axis with "Servo Here"
        self.g.GCommand(f"SH{self.ch}")
        # set acceleration
        self.g.GCommand(f"AC{self.ch} 2000000")
        # set deceleration
        self.g.GCommand(f"DC{self.ch} 2000000")
        # set slew speed
        self.g.GCommand(f"SP{self.ch} 200000")

    async def home(self, force: bool = False):
        # home mode, begin move, wait until after move
        s = self.g.GCommand(f"HM{self.ch};BG{self.ch};AM{self.ch}")
        print(s) # TODO remove

    async def move_relative(self, distance: float):
        # TODO counts per degree
        # relative position mode, begin move, wait until after move
        s = self.g.GCommand(f"PR{self.ch} {round(distance)};BG{self.ch};AM{self.ch}")
        print(s) # TODO remove
    
    async def move_absolute(self, distance: float):
        # TODO counts per degree
        # absolute position mode, begin move, wait until after move
        s = self.g.GCommand(f"PA{self.ch} {round(distance)};BG{self.ch};AM{self.ch}")
        print(s) # TODO remove
    
    async def update_position(self) -> float:
        s = self.g.GCommand(f"TP{self.ch}")
        return float(s)
    
    async def update_status(self) -> int:
        try:
            if self.status == Axis.ERROR:
                # latch errors until cleared by a good move
                self.status = Axis.ERROR
            elif int(self.g.GCommand(f"TC")) > 0:
                self.status = Axis.ERROR
            elif int(self.g.GCommand(f"SC{self.ch}")) == 0:
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

    