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

    def read_input_file(self):
        pass

    def run_sequence(self):
        pass