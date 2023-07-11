import sys
sys.path.append(".") # TODO: unhack

from gui.app import App

if __name__ == "__main__":
    app = App()


### TODO list
# Galil motion control
# Jog buttons with radio selection
# Stabilize size of preview image
# ROI preview frame
#   input ROI pixels
#   display ROI, zoomed in but not smoothed (pixelated)
#   cross-cuts with axis labels
# display image statistics
#   centroid
#   FWHM (in px)
#   histogram of values
# draw ROI onto full frame, enabled with checkbox
# draw computed centroid onto full and ROI frames, enabled with checkbox
# 12-bit imaging
# implement auto-focus
# auto-center image button
# save in FITS format
# read in input configuration and table of wavelengths
# run on windows without wsl