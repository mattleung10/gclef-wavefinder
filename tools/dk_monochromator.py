import serial


# RS-232 Interface to Spectal Products DK Series Monochromator
class MonochromAdapter:
    def __init__(self, dev: str) -> None:
        self.port = serial.Serial(
            port=dev, baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=2, rtscts=True, dsrdtr=True
        )

    def terminal(self):
        while True:
            try:
                cmd = input("> ")
                if cmd == "exit":
                    self.port.close()
                    break
                if cmd:
                    cmd_list = [int(n) for n in cmd.split()]
                    msg = bytearray(cmd_list)
                    print("> 0x" + msg.hex())
                    self.port.write(msg)

                    res = self.port.read_until()
                    if res:
                        print("< 0x" + res.hex())
                        print("< " + str([int(n) for n in bytearray(res)]))
                    else:
                        print("No reply.")
            except Exception as e:
                print("Error: " + str(e))


if __name__ == "__main__":
    mono = MonochromAdapter("COM6")
    mono.terminal()