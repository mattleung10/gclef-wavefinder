from abc import ABC, abstractmethod


class Axis(ABC):
    """Model holds information about genetic Axis"""

    READY   = 0
    MOVING  = 1
    BUSY    = 2
    ERROR   = 3
    STATES = [READY, MOVING, BUSY, ERROR]

    def __init__(self, name: str, keyword: str) -> None:
        self.name = name
        self.keyword = keyword[:8] # limit to 8 chars
        self.position = 0.
        self.status = Axis.BUSY
        self.is_homed = False
        self.units: tuple[str, str] = ("", "")

    @abstractmethod
    async def home(self):
        """Home the axis"""
        pass

    @abstractmethod
    async def move_relative(self, distance: float):
        """Relative position move
        
        Args:
            distance: in millimeters or degrees
        """
        pass

    @abstractmethod
    async def move_absolute(self, distance: float):
        """Absolute position move
            
            Args:
                distance: in millimeters or degrees
        """
        pass

    @abstractmethod
    async def stop(self):
        """Stop!"""
        pass

    @abstractmethod
    async def update_position(self) -> float:
        """Update application model of position by querying device"""
        return self.position
    
    @abstractmethod    
    async def update_status(self) -> int:
        """Update application model of status by querying device"""
        return self.status
    
    @abstractmethod
    async def set_limits(self, low_limit: float | None = None, high_limit: float | None = None):
        """Set axis low and high movement limits
        
        Args:
            low_limit: minimum movement limit in mm or degrees or None to not set
            high_limit: maximum movement limit in mm or degrees or None to not set
        """
        pass

    @abstractmethod
    async def get_limits(self) -> tuple[float, float]:
        """Axis low and high movement limits

        Returns: tuple (low, high) of limits as floats
        """
        pass