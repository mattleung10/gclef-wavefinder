import argparse

from wavefinder.gui.app import App

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", nargs='?', default="config.toml",
                        help="TOML config file. See config.toml for more info.")
    cf = parser.parse_args().config_file
    app = App(cf)


### TODO list
# read in input configuration and table of wavelengths
# alpha shapes, better image masking
# 12-bit imaging
# Cross-cuts with axis labels
# histogram of values
# Stabilize size of preview image
