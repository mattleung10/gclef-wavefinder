from ..devices.Axis import Axis
from ..gui.config import Configuration


class Sequencer:
    def __init__(self, config: Configuration, axes: dict[str, Axis]) -> None:
        """Sequencer class

        Reads in a table of positions, wavelengths, orders, etc.
        At each position:
            - move to position
            - center image
            - focus
            - take 3 images: [negative offset, on focus, positive offset]
            - save images and any other data
        """
        self.config = config
        self.sequence: list[dict[str, float]] = list()
        self.axes = axes

    def read_input_file(self, filename: str):
        """Read input sequence file
        
        Args:
            filename: path to filename
        """
        with open(filename) as f:
            # reset the sequence
            self.sequence = list()
            # set headers, strip whitespace from header names
            header_line = f.readline()
            headers = [h.strip() for h in header_line.split(',')]

            # this loop will start with the 2nd line because the previous
            # readline has advanced the buffer's iterator0
            for line in f:
                # make a dict, using the header values
                d : dict[str, float] = {}
                for i, n in enumerate(line.split(',')):
                    d[headers[i]] = float(n)
                self.sequence.append(d)

    def run_sequence(self, output_dir: str):
        """Run sequence and store data in output directory
        
        Args:
            output_dir: path to output directory
        """

        for i, row in enumerate(self.sequence):
            print(self.axes)
            # move to position
            for col in row:
                # match header with motion axis
                a = self.axes.get(col)
                if a:
                    print(a)

