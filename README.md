# zaber-focus
Control Software for Zaber XYZ Focus Stage with Mightex Camera

## Prequisites
* Python 11 (Python 10 is probably enough)
* `python3-tk` package
* numpy

## Install & Setup (on WSL)
1. Clone repository:
    ```
    $ git clone git@github.com:Smithsonian/zaber-focus.git
    ```
1. Install drivers, following *Software Installation* (page 7) instructions in `CCDBufCamera_CDROM_181227/Documents/Mightex Buffer USB CCD Camera User Manual.pdf`
    - Alternatively, see `CCDBufCamera_CDROM_181227/Camera_Start_Guide.pdf` for a short version.
1. Make a Python virtual environment:
    ```
    $ python3 -m venv .venv
    ```
1. Activate environment:
    ```
    $ source .venv/bin/activate
    ```
1. Install dependencies:
    ```
    $ pip install pyusb numpy Pillow
    ```
1. Add user to `plugdev` group:
    ```
    $ sudo usermod -a -G plugdev <username>
    ```
1. Log out and log back in to set new group membership. Check group membership for `plugdev`:
    ```
    $ groups
    ```
1. Install udev rule:
    ```
    $ sudo cp 10-local.rules /etc/udev/rules.d/
    ```
1. On host machine, install https://github.com/dorssel/usbipd-win

    Short version: in an *Admin Powershell* terminal:
    ```
    > winget install usbipd
    ```
1. Reboot host machine.
1. Plug in (or re-plug) Mightex camera USB.
1. Attach USB device to WSL. In an *Admin Powershell* terminal:
    ```
    > usbipd wsl list
    > usbipd wsl attach --busid <busid>
1. Check USB device in WSL (look for device existence and correct permissions):
    ```
    $ lsusb
    $ dmesg
    $ ls -al /dev/bus/usb/001/
    ```
### Notes
* `lsusb` should show something like:
    ```
    Bus 001 Device 002: ID 04b4:0528 Cypress Semiconductor Corp. USB-BUF-CCD-1
    ```
* `dmesg` should show something like:
    ```
    [ 8162.977561] usb 1-1: new high-speed USB device number 2 using vhci_hcd
    [ 8163.137663] usb 1-1: SetAddress Request (2) to port 0
    [ 8163.170946] usb 1-1: New USB device found, idVendor=04b4, idProduct=0528, bcdDevice= 0.00
    [ 8163.171465] usb 1-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
    [ 8163.171757] usb 1-1: Product: USB-BUF-CCD-1
    [ 8163.171905] usb 1-1: Manufacturer: Mightex
    ```

## Mightex SDK and Documentation
See folder `CCDBufCamera_CDROM_181227` for Mightex SDK and documentation. Some key files:
* `CCDBufCamera_CDROM_181227/Camera_Start_Guide.pdf`: quick start guide
* `CCDBufCamera_CDROM_181227/Documents/Mightex Buffer USB CCD Camera User Manual.pdf`: how to install drivers and use the included example program
* `CCDBufCamera_CDROM_181227/SDK/Documents/Mightex Buffer USB CCD Camera USB Protocol.pdf`: USB protocol information (used to make this application)

### Data Structures from Mightex Camera
```
Typedef struct
{
  tUINT16 Row;
  tUINT16 Column;
  tUINT16 Bin;
  tUINT16 XStart;
  tUINT16 YStart;
  tUINT16 RedGain;
  tUINT16 GreenGain;
  tUINT16 BlueGain;
  tUINT16 TimeStamp;
  tUINT16 TriggerEventOccurred;
  tUINT16 TriggerEventCount;
  tUINT16 UserMark;
  tUINT16 FrameTime;
  tUINT16 CCDFrequency;
  tUINT32 ExposureTime;
  tUINT16 Reserved[240];
} tFrameProperty; // Note: Sizeof (tFrameProperty) is 512 byte.
```
```
Typedef struct
{
  // For 8bit mode, e.g. PixelData[1040][1392] for CCX-B013-U module, PixelData[960][1280] for CGX
  // modules.
  tUINT8 PixelData[RowNumber][ColumnNumber];
  /*
  * For 12bit mode, we have the following:
  * tUINT8 PixelData[RowNumber][ColumnNumber][2]; // 12 bit camera
  * and PixelData[][][0] contains the 8bit MSB of 12bit pixel data, while the 4 LSB of PixelData[][][1] has
  * the 4bit LSB of the 12bit pixel data.
  */
  tUINT8 Paddings[]; // Depends on different resolution.
  tFramePropery ImageProperty; // Note: Sizeof (tFrameProperty) is 512 byte.
} tImageFrame;
```
```
#define STRING_LENGTH 14
typedef struct
{
  BYTE ConfigRevision;
  BYTE ModuleNo[STRING_LENGTH];
  BYTE SerialNo[STRING_LENGTH];
  BYTE ManuafactureDate[STRING_LENGTH];
} tDeviceInfo;
```
