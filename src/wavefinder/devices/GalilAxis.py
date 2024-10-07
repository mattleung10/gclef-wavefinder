import asyncio

from gclib import GclibError, py

from .Axis import Axis


class GalilAxis(Axis):
    # Galil implementation of Axis superclass
    # See Axis for abstract function descriptions.

    def __init__(
        self,
        name: str,
        keyword: str,
        channel: str,
        connection: py,
        accel: int = 2000000,
        decel: int = 2000000,
        speed: int = 100000,
        homing_speed: int = 5000,
        encoder_counts_per_degree: int = 800,
        drive_counts_per_degree: int = 10000,
    ) -> None:
        """Zaber motion control axis

        Args:
            name: human-readable name of axis
            keyword: FITS keyword
            channel: axis channel (A, B, C, D)
            connection: gclib py object with open connection
            accel: acceleration
            decel: deceleration
            speed: move speed
            homing_speed: homing speed
            encoder_counts_per_degree: encoder counts per degree
            encoder_counts_per_degree: drive counts per degree
        """
        super().__init__(name, keyword)
        self.ch = channel
        self.g = connection
        self.accel = accel
        self.decel = decel
        self.speed = speed
        self.hspeed = homing_speed
        self.encoder_scale = encoder_counts_per_degree
        self.drive_scale = drive_counts_per_degree
        self.units = ("deg", "arc degrees")  # NOTE: hardcoded units

        # enable axis with "Servo Here"
        self.g.GCommand(f"SH{self.ch}")
        # set acceleration, decleration, slew speed
        self.g.GCommand(f"AC{self.ch}={self.accel}")
        self.g.GCommand(f"DC{self.ch}={self.decel}")
        self.g.GCommand(f"SP{self.ch}={self.speed}")
        # NOTE: HV is most likely not doing anything because these are stepper
        #       motors, but we still use hspeed in our homing routine.
        self.g.GCommand(f"HV{self.ch}={self.hspeed}")

    async def home(self):
        try:
            self.status = Axis.BUSY
            # if at negative limit, move off limit
            negative_limited = not bool(float(self.g.GCommand(f"MG _LR{self.ch}")))
            if negative_limited:
                counts = 30000  # NOTE: from provided #HOME function
                self.g.GCommand(f"PR{self.ch}={counts};BG{self.ch}")
                await self.wait_for_motion_complete(self.ch)
            # jog negative until limit
            self.g.GCommand(f"JG{self.ch}=-{self.speed};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # home
            self.g.GCommand(f"HM{self.ch};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # slow down to hspeed
            self.g.GCommand(f"SP{self.ch}={self.hspeed}")
            # move 1 count
            self.g.GCommand(f"PR{self.ch}=1;BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # find motor index
            self.g.GCommand(f"FI{self.ch};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            # wait half a second
            await asyncio.sleep(0.5)
            # zero position
            self.g.GCommand(f"DP{self.ch}=0")
            self.g.GCommand(f"DE{self.ch}=0")
            # resume normal speed
            self.g.GCommand(f"SP{self.ch}={self.speed}")
            # update
            await self.update_position()
            await self.update_status()
        except GclibError:
            self.status = Axis.ERROR

    async def move_relative(self, distance: float):
        try:
            self.status = Axis.MOVING
            counts = round(distance * self.drive_scale)
            self.g.GCommand(f"PR{self.ch}={counts};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            await self.update_position()
            await self.update_status()
        except GclibError:
            self.status = Axis.ERROR

    async def move_absolute(self, position: float):
        try:
            self.status = Axis.MOVING
            counts = round(position * self.drive_scale)
            self.g.GCommand(f"PA{self.ch}={counts};BG{self.ch}")
            await self.wait_for_motion_complete(self.ch)
            await self.update_position()
            # NOTE: drive is not using encoder as feedback, so friction can
            # cause an small error which we correct here.
            # Find the error in drive counts, then if error is larger than
            # drive counts per encoder count, make a big move;
            # else, move one drive count at a time until error is zero.
            while round(self.position, 3) != round(position, 3):
                err_counts = int((position - self.position) * self.drive_scale)
                if err_counts > self.drive_scale / self.encoder_scale:
                    self.g.GCommand(f"YR{self.ch}={err_counts}")
                    await self.wait_for_motion_complete(self.ch)
                    await self.update_position()
                else:
                    # get the sign of the error, yielding -1 or 1
                    step = int(err_counts / abs(err_counts))
                    self.g.GCommand(f"YR{self.ch}={step}")
                    await self.wait_for_motion_complete(self.ch)
                    await self.update_position()
            await self.update_status()
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
            await self.update_position()
            await self.update_status()
        except GclibError:
            self.status = Axis.ERROR

    async def update_position(self) -> float:
        p = float(self.g.GCommand(f"TP{self.ch}"))
        self.position = p / self.encoder_scale
        return self.position

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

    async def set_limits(
        self, low_limit: float | None = None, high_limit: float | None = None
    ):
        try:
            if low_limit is not None:
                self.g.GCommand(f"BL{self.ch}={low_limit * self.drive_scale}")
            if high_limit is not None:
                self.g.GCommand(f"FL{self.ch}={high_limit * self.drive_scale}")
        except GclibError:
            self.status = Axis.ERROR

    async def get_limits(self) -> tuple[float, float]:
        l = 0.0
        h = 0.0
        try:
            l = float(self.g.GCommand(f"BL{self.ch}=?")) / self.drive_scale
            h = float(self.g.GCommand(f"FL{self.ch}=?")) / self.drive_scale
        except GclibError:
            self.status = Axis.ERROR
        return (l, h)
