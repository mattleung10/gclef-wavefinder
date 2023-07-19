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

    @abstractmethod
    async def home(self):
        pass

    @abstractmethod
    async def move_relative(self, distance : float):
        pass

    @abstractmethod
    async def move_absolute(self, distance : float):
        pass

    @abstractmethod
    async def get_position(self) -> float:
        return self.position
    
    @abstractmethod    
    async def get_status(self):
        return self.status
    
    @abstractmethod
    async def set_limits(self, high_limit : float, low_limit :float):
        pass