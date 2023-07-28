import asyncio

from zaber_motion import ConnectionFailedException, MotionLibException
from zaber_motion.ascii import Connection, Device

from .ZaberAxis import ZaberAxis


class ZaberAdapter:
    """Interface adapter between application and zaber library"""

    def __init__(self, port_names: list[str],
                 axis_names: dict[str, tuple[int, int]]) -> None:
        """Set up adapter with all devices' axes visible from port

        Args:
            port_names: list of ports, e.g. ['/dev/ttyUSB0', '/dev/ttyUSB1']
            axis_names: mapping of name to axis (device serial number, axis number)
                e.g. {"x": (33938, 1), "y": (33937, 1)}
        """

        self.port_names = port_names
        self.axis_names = axis_names
        self.connections: list[Connection] = []
        self.device_list: list[Device] = []
        self.axes: dict[str, ZaberAxis] = {}

        for p in self.port_names:
            print(f"Connecting to Zaber devices on {p}... ", end='', flush=True)
            try:
                c = Connection.open_serial_port(p)
                c.enable_alerts()
                self.connections.append(c)
                self.device_list.extend(c.detect_devices())
            except ConnectionFailedException as e:
                print(e.message)
                continue
            else:
                print("connected.")
        
        if len(self.device_list) == 0:
            return

        for a in self.axis_names.keys():
            sn = self.axis_names[a][0] # serial number
            an = self.axis_names[a][1] # axis number
            print(f"Finding {a} {(sn,an)}...", end='', flush=True)
            try:
                device: Device = next(filter(lambda d: d.serial_number == sn,
                                             self.device_list))
                axis = device.get_axis(an)
                self.axes[a] = ZaberAxis(a, axis)
            except StopIteration:
                print("not found.") # device not found
            except ValueError:
                print("not found.") # axis number bad
            except MotionLibException:
                print("not found.") # axis not functional
            except Exception as e:
                print(e) # can't make Axis, other errors
            else:
                print("OK.")

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
    
    def close(self):
        """Close adapter"""
        for con in self.connections:
            con.close()