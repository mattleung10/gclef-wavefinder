from gclib import GclibError, py

from ..gui.utils import Cyclic
from .GalilAxis import GalilAxis


class GalilAdapter(Cyclic):
    """Interface adapter between application and galil"""

    def __init__(
        self,
        address: str,
        axis_names: dict[str, dict[str, str]],
        accel: int = 2000000,
        decel: int = 2000000,
        speed: int = 100000,
        homing_speed: int = 5000,
        encoder_counts_per_degree: int = 800,
        drive_counts_per_degree: int = 10000,
    ) -> None:
        """Set up adapter with all devices' axes visible from controller

        Args:
            address: IP address of controller as string, e.g. "192.168.1.19"
            axis_names: mapping of name to axis channel identifier and keyword
                e.g. {"cfm1 azimuth": {"ch": "A", "keyword": "cfm1az"}}
            accel: acceleration
            decel: deceleration
            speed: move speed
            homing_speed: homing speed
            encoder_counts_per_degree: encoder counts per degree
            encoder_counts_per_degree: drive counts per degree
        """
        self.address = address
        self.axis_names = axis_names
        self.axes: dict[str, GalilAxis] = {}

        print(f"Connecting to Galil devices on {address}... ", end="", flush=True)
        try:
            self.g = py()
            # connect in direct mode, subscribe to all unsolicited, 1000ms second timeout
            self.g.GOpen(f"{self.address} -d -s ALL -t 1000")
        except GclibError as e:
            print(e)
            return
        else:
            print("connected.")

        for name in self.axis_names.keys():
            ch = self.axis_names[name]["ch"]  # channel
            kw = self.axis_names[name]["keyword"]
            print(f"Finding {name} on channel {ch}... ", end="", flush=True)
            try:
                self.axes[name] = GalilAxis(
                    name,
                    kw,
                    ch,
                    self.connection,
                    accel,
                    decel,
                    speed,
                    homing_speed,
                    encoder_counts_per_degree,
                    drive_counts_per_degree,
                )
            except GclibError:
                print("not found.")  # device not found
            except Exception as e:
                print(e)  # can't make Axis, other errors
            else:
                print("OK.")

    @property
    def connection(self) -> py:
        return self.g

    async def update(self):
        """Update all devices on this adapter"""
        for a in self.axes.values():
            await a.update_position()
            await a.update_status()

    def close(self):
        """Close adapter"""
        self.g.GClose()
