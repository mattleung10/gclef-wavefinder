import asyncio

import gclib.gclib as gclib
from .GalilAxis import GalilAxis

class GalilAdapter:
    """Interface adapter between application and galil"""
    def __init__(self, address: str,
                 axis_names: dict[str, str]) -> None:
        """Set up adapter with all devices' axes visible from controller

        Args:
            address: IP address of controller as string, e.g. "192.168.1.19"
            axis_names: mapping of name to axis channel identifier
                e.g. {"gimbal 1 elevation": "A", "gimbal 2 azimuth": "D"}
        """

        self.address = address
        self.axis_names = axis_names
        self.axes: dict[str, GalilAxis] = {}
        
        print(f"Connecting to Galil devices on {address}... ", end='')
        try:
            self.g = gclib.py()
            self.g.GOpen(self.address + " -s ALL")
        except gclib.GclibError as e:
            print(e)
            return
        else:
            print("connected.")
        
        for a_nm, a_ch in self.axis_names.items():
            print(f"Finding {a_nm} on channel {a_ch}... ", end='')
            try:
                self.axes[a_nm] = GalilAxis(a_nm, a_ch, self.g)
            except gclib.GclibError:
                print("not found.") # device not found
            except Exception as e:
                print(e) # can't make Axis, other errors
            else:
                print("OK.")

    @property
    def connection(self) -> gclib.py:
        return self.g

    async def update(self):
        """Update all devices on this adapter"""
        for a in self.axes.values():
            await a.update_position()
            await a.update_status()

    async def update_loop(self, interval: float = 1):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
           await asyncio.gather(self.update(), asyncio.sleep(interval))
