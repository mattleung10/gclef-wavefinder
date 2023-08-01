from zaber_motion.ascii import Connection, Device
from zaber_motion import ConnectionFailedException

device_list: list[Device] = []

for p in ['COM3', 'COM6']:
    print(f"Connecting to Zaber devices on {p}... ", end='', flush=True)
    try:
        c = Connection.open_serial_port(p)
        c.enable_alerts()
        device_list.extend(c.detect_devices())
    except ConnectionFailedException as e:
        print(e.message)
        continue
    else:
        print("connected.")

for d in device_list:
    d.generic_command("system restore")
    # d.generic_command("system reset")