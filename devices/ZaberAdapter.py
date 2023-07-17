from zaber_motion import Units
from zaber_motion.ascii import Axis, Connection, Device


class ZaberAxis:
    """Model holds information about Zaber Axis"""

    READY   = 0
    MOVING  = 1
    BUSY    = 2
    ERROR   = 3

    def __init__(self, name : str, axis : Axis) -> None:
        self.name = name
        self.axis = axis
        self.position = 0.
        self.status = ZaberAxis.ERROR

    @property
    def serial_number(self) -> int:
        return self.axis.device.serial_number

    @property
    def axis_number(self) -> int:
        return self.axis.axis_number


class ZaberAdapter:
    """Interface adapter between application and zaber library"""

    def __init__(self, port_names : list[str],
                 axis_names : dict[str,tuple[int,int]]) -> None:
        """Set up adapter with all devices' axes visible from port

        Args:
            port_name: name of port, e.g. '/dev/ttyUSB0'
            axis_names: mapping of name to axis (device serial number, axis number)
                e.g. {"x" : (33938, 1), "y" : (33937, 1)}
        """

        self.axis_names = axis_names
        self.connections : list[Connection] = []
        self.device_list : list[Device] = []
        self.axes : dict[str,ZaberAxis] = {}

        print("Connecting to Zaber devices... ", end='')
        for p in port_names:
            c = Connection.open_serial_port(p)
            c.enable_alerts()
            self.connections.append(c)
            self.device_list.extend(c.detect_devices())
        print("connected.")

        for a in axis_names.keys():
            sn = axis_names[a][0] # serial number
            an = axis_names[a][1] # axis number
            print("Finding " + a + " " + str((sn,an))  + "... ", end='')
            try:
                device : Device = next(filter(lambda d: d.serial_number == sn,
                                                self.device_list))
                axis = device.get_axis(an)
                self.axes[a] = ZaberAxis(a, axis)
                print("OK.")
            except StopIteration:
                print("not found.") # device not found
            except ValueError as e:
                print(e) # axis number bad
            except Exception as e:
                print(e) # can't make AxisModel, other errors

    def set_axis_setting(self, serial_number : int, axis_number : int,
                         setting : str, value : float, unit : Units) -> bool:
        """Set a setting on an axis

        Args:
            serial_number: device serial number
            axis_number: axis number on device
            setting: setting name
            value: value to set
            unit: unit of setting value

        Returns:
            True if successful; False if failed
        """
        try:
            device : Device = next(filter(lambda d: d.serial_number == serial_number,
                                        self.device_list))
            axis : Axis = device.get_axis(axis_number)
            axis.settings.set(setting=setting, value=value, unit=unit)
            return True
        except Exception:
            return False