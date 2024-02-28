import argparse

from wavefinder.gui.app import App

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        nargs="?",
        default="config.toml",
        help="TOML config file. See config.toml for more info.",
    )
    cf = parser.parse_args().config_file
    app = App(cf)
