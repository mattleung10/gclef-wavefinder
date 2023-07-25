# A simple interactive terminal for commanding the Galil/Newmark controller

import gclib

g = gclib.py()
g.GOpen('192.168.1.19 -d -s ALL')

while True:
    try:
        cmd = input("> ")
        if cmd == "exit":
            g.GClose()
            break
        res = g.GCommand(cmd)
        print("< " + res)
    except gclib.GclibError as e:
        print("Error: " + str(e))
        s = g.GCommand(f"TC1")
        print("Error Code: " + s)