import serial


# RS-232 Interface to Spectal Products DK Series Monochromator
class DkAdapter:
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
                    # read in list of ints, convert to byte array
                    cmd_list = [int(n) for n in cmd.split()]
                    msg = bytearray(cmd_list)
                    # echo byte array and send to device
                    print("> 0x" + msg.hex())
                    self.port.write(msg)

                    # read bytes until timeout
                    res = self.port.read_until()
                    if res:
                        # echo raw byte array and array of converted ints
                        print("< 0x" + res.hex())
                        print("< " + str([int(n) for n in bytearray(res)]))
                    else:
                        print("No reply.")
            except Exception as e:
                print("Error: " + str(e))


if __name__ == "__main__":
    mono = DkAdapter("COM6")
    mono.terminal()