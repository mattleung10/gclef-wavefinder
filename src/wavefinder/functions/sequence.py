from ..gui.config import Configuration


class Sequencer:
    def __init__(self, config: Configuration) -> None:
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

    def read_input_file(self, filename: str):
        """Read input sequence file
        
        Args:
            filename: path to filename
        """
        print(filename)

    def run_sequence(self, output_dir: str):
        """Run sequence and store data in output directory
        
        Args:
            output_dir: path to output directory
        """
        print(output_dir)
