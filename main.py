import sys
sys.path.append(".") # TODO: unhack

from gui.app import App

if __name__ == "__main__":
    app = App()


### TODO list
# Galil motion control
# Cross-cuts with axis labels
# histogram of values
# 12-bit imaging
# save in FITS format
# Stabilize size of preview image
# read in input configuration and table of wavelengths
# run on windows without wsl