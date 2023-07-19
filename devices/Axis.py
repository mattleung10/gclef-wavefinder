from abc import ABC, abstractmethod

class Axis(ABC):
    """Model holds information about genetic Axis"""

    READY   = 0
    MOVING  = 1
    BUSY    = 2
    ERROR   = 3
    STATES = [READY, MOVING, BUSY, ERROR]

    def __init__(self, name : str) -> None:
        self.name = name
        self.position = 0.
        self.status = Axis.ERROR
        self.is_homed = False

    @abstractmethod
    async def home(self, force : bool = False):
        """Home the axis if necessary
        
        Args:
            force: perform homing even if not needed
        """
        pass

    @abstractmethod
    async def move_relative(self, distance : float):
        """Relative position move
        
        Args:
            distance: in millimeters
        """
        pass

    @abstractmethod
    async def move_absolute(self, distance : float):
        """Absolute position move
            
            Args:
                distance: in millimeters
        """
        pass

    @abstractmethod
    async def get_position(self) -> float:
        """Get position from device"""
        return self.position
    
    @abstractmethod    
    async def get_status(self):
        """Get status from device"""
        return self.status
    
    @abstractmethod
    async def set_limits(self, low_limit : float|None = None, high_limit : float|None = None):
        """Set axis low and high movement limits
        
        Args:
            low_limit: minimum movement limit in mm or None to not set
            high_limit: maximum movement limit in mm or None to not set
        """
        pass

    @abstractmethod
    async def get_limits(self) -> tuple[float, float]:
        """Axis low and high movement limits

        Returns: tuple (low, high) of limits as floats
        """
        pass