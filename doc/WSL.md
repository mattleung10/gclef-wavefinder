# Additional Steps for WSL
1. Follow installation instructions in previous section.
1. Add user to `plugdev` and `dialout` groups:
    ```
    $ sudo usermod -a -G plugdev <username>
    $ sudo usermod -a -G dialout <username>
    ```
1. Log out and log back in to set new group membership.
    ```
    $ groups
    ```
1. Install udev rule:
    ```
    $ sudo cp sys/Linux/10-local.rules /etc/udev/rules.d/
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
1. Similarly, `usbipd wsl attach` the USB devices corresponding to `/dev/ttyUSB0` and `/dev/ttyUSB1`. These should be called something like "USB Serial Converter" in `usbipd wsl list`.

## Notes
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
