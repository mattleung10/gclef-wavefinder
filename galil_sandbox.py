import gclib.gclib as gclib
import traceback

g = gclib.py()
g.GOpen('192.168.1.19 -d -s ALL')

# Homing sequence:
# 0) Configure: enable servo, accel, decel, slew speed, home speed, limit switch polarity
# 1) jog negative until limit, if not already at limit
# 2) Home command
# 3) Define Encoder Position 0

ch = "D"
try:
    # configure
    g.GCommand(f"SH{ch}")         # enable servo
    g.GCommand(f"AC{ch}=2000000") # acceleration
    g.GCommand(f"DC{ch}=2000000") # deceleration
    g.GCommand(f"SP{ch}=200000")  # slew speed
    g.GCommand(f"CN 1,-1")        # config switches: limit active high, home "0 when grounded (or active-opto)" 

    # status
    ts = int(g.GCommand(f"TS{ch}"))
    lr = ts & 0b00000100
    print(f"switches: {ts:08b}")
    tp = g.GCommand(f"TP{ch}")
    print(f"position: {tp}")

    # jog negative
    if lr:
        g.GCommand(f"JG{ch}=-100000")
        g.GCommand(f"BG{ch}")
        g.GMotionComplete(f"{ch}")
        print("found negative limit")

        # status
        ts = int(g.GCommand(f"TS{ch}"))
        print(f"switches: {ts:08b}")
        tp = g.GCommand(f"TP{ch}")
        print(f"position: {tp}")
    else:
        print("already at negative limit")

    # home
    g.GCommand(f"HV{ch}=5000")
    g.GCommand(f"HM{ch}")
    g.GCommand(f"BG{ch}")
    g.GMotionComplete(f"{ch}")
    g.GCommand(f"DE{ch}=0")
    print("home")

    # status
    ts = int(g.GCommand(f"TS{ch}"))
    print(f"switches: {ts:08b}")
    tp = g.GCommand(f"TP{ch}")
    print(f"position: {tp}")

except gclib.GclibError as e:
    s = g.GCommand(f"TC1")
    g.GClose()
    print(s)
    print(traceback.format_exception(e))
