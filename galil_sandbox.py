import gclib.gclib as gclib

g = gclib.py()
g.GOpen('192.168.1.19')

ch = "A"
g.GCommand(f"AC{ch}=2000000")
print("1")
g.GCommand(f"DC{ch}=2000000")
print("2")
g.GCommand(f"SP{ch}=200000")
print("3")

g.GCommand(f"PA{ch}=10000")
print("4")
g.GCommand(f"BG{ch}")
print("5")
g.GCommand(f"AM{ch}")
print("6")

# Home
g.GCommand(f"HM{ch}")
print("4")
g.GCommand(f"BG{ch}")
print("5")
g.GCommand(f"AM{ch}")
print("6")
