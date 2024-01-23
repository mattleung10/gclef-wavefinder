# Mightex Camera Information
## Mightex SDK and Documentation
See folder `Mightex_SDK` for Mightex SDK and documentation. Some key files:
* `Mightex_SDK/Camera_Start_Guide.pdf`: quick start guide
* `Mightex_SDK/Documents/Mightex Buffer USB CCD Camera User Manual.pdf`: how to install drivers and use the included example program
* `Mightex_SDK/SDK/Documents/Mightex Buffer USB CCD Camera USB Protocol.pdf`: USB protocol information (used to make this application)
* `Mightex_SDK/Driver/Windows7/`: included driver files; DO NOT USE, see [Drivers](#drivers).

## Data Structures from Mightex Camera
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
