from zaber_motion import MotionLibException
from zaber_motion.ascii import Connection, Device

from ..gui.utils import Cyclic
from .ZaberAxis import ZaberAxis


class ZaberAdapter(Cyclic):
    """Interface adapter between application and zaber library"""

    def __init__(
        self, port_names: list[str] | str, axis_names: dict[str, dict[str, int | str]]
    ) -> None:
        """Set up adapter with all devices' axes visible from port

        Args:
            port_names: list of ports, e.g. ['/dev/ttyUSB0', '/dev/ttyUSB1']
            axis_names: "name" = {sn = serial_number, keyword = "kw"}
                        e.g. {"detector x": {"sn": 33938, "keyword": "detxpos"}}
        """

        self.port_names = port_names if isinstance(port_names, list) else [port_names]
        self.axis_names = axis_names
        self.connections: list[Connection] = []
        self.device_list: list[Device] = []
        self.axes: dict[str, ZaberAxis] = {}

        for p in self.port_names:
            print(f"Connecting to Zaber devices on {p}... ", end="", flush=True)
            try:
                c = Connection.open_serial_port(p, direct=True)
                c.enable_alerts()
                self.connections.append(c)
                self.device_list.extend(c.detect_devices())
            except MotionLibException as e:
                print(e.message)
                continue
            else:
                print("connected.")

        if len(self.device_list) == 0:
            return

        for name in self.axis_names.keys():
            sn = int(self.axis_names[name]["sn"])  # serial number
            kw = str(self.axis_names[name]["keyword"])
            print(f"Finding {name} ({sn})...", end="", flush=True)
            try:
                device: Device = next(
                    filter(lambda d: d.serial_number == sn, self.device_list)
                )
                # NOTE: we always use axis #1 because all our devices have only one axis,
                #       but if you want to change that, do that here.
                axis = device.get_axis(1)
                self.axes[name] = ZaberAxis(name, kw, axis)
            except StopIteration:
                print("not found.")  # device not found
            except ValueError:
                print("not found.")  # axis number bad
            except MotionLibException:
                print("not found.")  # axis not functional
            except Exception as e:
                print(e)  # can't make Axis, other errors
            else:
                print("OK.")

    async def update(self):
        """Update all devices on this adapter"""
        for a in self.axes.values():
            await a.update_position()
            await a.update_status()

    def close(self):
        """Close adapter"""
        for con in self.connections:
            con.close()
