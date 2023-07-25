# A simple interactive terminal for commanding the Galil/Newmark controller

import gclib.gclib as gclib

g = gclib.py()
g.GOpen('192.168.1.19 -d -s ALL')

while True:
    cmd = input("> ")
    if cmd == "exit":
        break
    res = g.GCommand(cmd)
    print("< " + res)
    g.GMotionComplete("")
