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

    async def home(self, force: bool = False):
        pass

    async def move_relative(self, distance: float):
        pass
    
    async def move_absolute(self, distance: float):
        pass
    
    async def update_position(self) -> float:
        return 0.0
    
    async def update_status(self) -> int:
        return Axis.ERROR
    
    async def set_limits(self, low_limit: float | None = None, high_limit: float | None = None):
        pass
    
    async def get_limits(self) -> tuple[float, float]:
        return (0., 0.)

    