# G-CLEF Wavefinder User Guide
## Table of Contents

## Software Prequisites and Installation
See [README.md](../README.md) for [Prequisites](../README.md#prequisites) and [Installation](../README.md#installation).

## Hardware Setup
* mightex
* zaber
* galil
* USB hub

## Run the Application
* run from Powershell
* terminal messages and information
    * connections and devices found
    * camera setup
    * errors and warnings
* close the application

## Configuration
* Running with a different config file
* important parameters:
    * ports and connectivity
    * axis names
    * motion limits
    * camera parameters
    * image parameters
    * focus parameters

## Application Information
* Python async is not multi-threaded
* update_rate

## Working with the Mightex Camera
* detector properties
* normal vs streaming modes
* 8 vs 12 bit modes
* resolution
* binning
* exposure time
* frames per second
* gain
* frequency
* writing to camera
* camera buffer
* timestamp of frames

## Working with Motion Stages
* connectivity
    * zaber
        * serial numbers
    * numark/galil
* axis names
* motion limits
* moving
* jogging
* status colors
* clearing errors
* homing
* reading back position
* recording position in FITS files
* "copy position"
* "zero inputs"

## Camera Frame
* image properties
* full frame preview
* histogram
    * limit to threshold

## Region of Interest
* set ROI size
* set ROI zoom
* cross-cuts
* histogram
    * limit to threshold

## Functions
* capture image
    * obs type
    * target name
* save image to FITS file
* set thresholds
    * full frame
    * ROI
* switch calculation mode between full-frame & ROI
* image statistics
    * centroid
    * full-width half-maximum
        * method selection and description of each method
    * saturated pixels
* auto-center
* auto-focus
    * set exposure and threshold for best results
* sequences

## Tutorials
### Center and Focus a Spot
### Run a Sequence of Observations