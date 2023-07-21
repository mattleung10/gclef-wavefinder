from .Axis import Axis

from zaber_motion.ascii import Axis as ZAxis
from zaber_motion import Units, MotionLibException

class ZaberAxis(Axis):
    # Zaber implementation of Axis superclass
    # See Axis for abstract function descriptions.

    def __init__(self, name: str, axis_handle: ZAxis) -> None:
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
    
    async def home(self, force: bool = False):
        try:
            if force or not await self.axis.is_homed_async():
                self.status = Axis.BUSY
                await self.axis.home_async()
                await self.update_position()
                await self.update_status()
        except MotionLibException:
            self.status = Axis.ERROR

    async def move_relative(self, distance: float):
        try:
            self.status = Axis.MOVING
            await self.axis.move_relative_async(distance, Units.LENGTH_MILLIMETRES)
            await self.update_position()
            await self.update_status()
        except MotionLibException:
            self.status = Axis.ERROR

    async def move_absolute(self, distance: float):
        try:
            self.status = Axis.MOVING
            await self.axis.move_absolute_async(distance, Units.LENGTH_MILLIMETRES)
            await self.update_position()
            await self.update_status()
        except MotionLibException:
            self.status = Axis.ERROR

    async def update_position(self) -> float:
        try:
            self.position = await self.axis.get_position_async(Units.LENGTH_MILLIMETRES)
        except MotionLibException:
            self.status = Axis.ERROR
        return self.position
      
    async def update_status(self) -> int:
        try:
            if self.status == Axis.ERROR:
                # latch errors until cleared by a good move
                self.status = Axis.ERROR
            elif await self.axis.warnings.get_flags_async():
                self.status = Axis.ERROR
            elif await self.axis.is_busy_async():
                self.status = Axis.BUSY
            else:
                self.status = Axis.READY
        except MotionLibException:
            self.status = Axis.ERROR
        return self.status
    
    async def set_limits(self, low_limit: float | None = None, high_limit: float | None = None):
        try:
            if low_limit:
                await self.axis.settings.set_async('limit.min', low_limit,  Units.LENGTH_MILLIMETRES)
            if high_limit:
                await self.axis.settings.set_async('limit.max', high_limit, Units.LENGTH_MILLIMETRES)
        except MotionLibException:
            self.status = Axis.ERROR

    async def get_limits(self) -> tuple[float, float]:
        l = 0.
        h = 0.
        try:
            l = await self.axis.settings.get_async('limit.min', Units.LENGTH_MILLIMETRES)
            h = await self.axis.settings.get_async('limit.max', Units.LENGTH_MILLIMETRES)
        except MotionLibException:
            self.status = Axis.ERROR
        return (l, h)
