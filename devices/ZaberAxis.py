from Axis import Axis

from zaber_motion.ascii import Axis as ZAxis
from zaber_motion import Units

class ZaberAxis(Axis):
    # Zaber implementation of Axis superclass
    # See Axis for abstract function descriptions.

    def __init__(self, name: str, axis_handle : ZAxis) -> None:
        """Zaber motion control axis
        
        Args:
            name: human-readable name of axis
            axis_handle: zaber_motion Axis object
        """
        super().__init__(name)
        self.axis = axis_handle

    @property
    def serial_number(self) -> int:
        return self.axis.device.serial_number

    @property
    def axis_number(self) -> int:
        return self.axis.axis_number
    
    async def home(self, force : bool = False):
        if force or not await self.axis.is_homed_async():
            await self.axis.home_async()

    async def move_relative(self, distance : float):
        await self.axis.move_relative_async(distance, Units.LENGTH_MILLIMETRES)

    async def move_absolute(self, distance : float):
        await self.axis.move_absolute_async(distance, Units.LENGTH_MILLIMETRES)

    async def get_position(self) -> float:

        
        return self.position
      
    async def get_status(self) -> int:
        if await self.axis.warnings.get_flags_async():
            self.status = Axis.ERROR
        elif await self.axis.is_busy_async():
            self.status = Axis.BUSY
        else:
            self.status = Axis.READY
        return self.status
    
    async def get_warnings(self):
        """Get warning flags from device."""
        return await self.axis.warnings.get_flags_async()
    
    async def set_limits(self, high_limit : float, low_limit :float):
        pass