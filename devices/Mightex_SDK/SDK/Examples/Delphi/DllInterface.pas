unit DllInterface;

interface

uses windows, graphics, DataTypes;

type

  PImageControl = ^TImageControl;
  TImageControl = packed record
    Revision : integer;
    // Camera Device Ino
    DeviceType : eDEVICETYPE;
    Reserved1: Array[0..7] of Byte;
    // Row/Column are also reserved.
    Reserved2: integer;
    Reserved3: integer;
    // For Image Capture
    WorkMode : eWORKMODE;
    Resolution : integer;
    ExposureTime : integer;
    Bin    : integer;
    BinMode: integer; // If Bin isn't 0, BinMode indicates Skip(0) or Bin(1).
    XStart : integer;
    YStart : integer;
    RedGain: integer;
    GreenGain : integer;
    BlueGain : integer;
    BufferCnt : integer;
    BufferOption : integer;
    // GPIO Control
    GpioConfigByte: Byte; // Config for Input/Output for each pin.
    GpioCurrentSet: Byte; // For output Pins only.
  end;

  PProcessedDataProperty = ^TProcessedDataProperty;
  TProcessedDataProperty = record
    CameraID     : integer;
    Row          : integer;
    Column       : integer;
    Bin          : integer;
    XStart       : integer;
    YStart       : integer;
    ExposureTime : integer;
    RedGain      : integer;
    GreenGain    : integer;
    BlueGain     : integer;
    TimeStamp    : integer;
    TriggerOccurred  : integer;
    TriggerEventCount: integer;
    UserMark : integer;
    FrameTime : integer;
    CCDFrequency : integer;

    ProcessFrameType : integer;
    FilterAcceptForFile : integer;
  end;

  TGetFrameCallBack = procedure( ImageProperty : PProcessedDataProperty ; FramePtr : PByte ); cdecl;
  TUSBDeviceCallBack = procedure( DeviceType: integer ); cdecl;

// General functions
function BUFUSBInitDevice() : integer; cdecl;
function BUFUSBUnInitDevice() : integer; cdecl;
function BUFUSBGetModuleNoSerialNo( deviceID : integer; ModuleNo : PAnsiChar; SerialNo : PAnsiChar ): integer; cdecl;
function BUFUSBGetUserSerialNo( deviceID : integer; UserSerialNo : PAnsiChar ): integer; cdecl;
function BUFUSBSetUserSerialNo( deviceID : integer; UserSerialNo : PAnsiChar; Store : integer ): integer; cdecl;
function BUFUSBAddDeviceToWorkingSet( deviceID : integer ) : integer; cdecl;
function BUFUSBRemoveDeviceFromWorkingSet( deviceID : integer ) : integer; cdecl;
function BUFUSBActivateDeviceInWorkingSet( deviceID : integer ; Active : integer ) : integer; cdecl;
function BUFUSBStartCameraEngine( ParentFormHandle : THandle ; CameraBitOption : integer ) : integer ; cdecl;
function BUFUSBStopCameraEngine() : integer ; cdecl;
function BUFUSBSetBayerFilterType( filterType : integer ) : integer ; cdecl;
function BUFUSBSetCameraWorkMode( DeviceID : integer ;
                                  WorkMode : Integer ) : integer; cdecl;
function BUFUSBStartFrameGrab( TotalFrames : Integer ) : integer ; cdecl;
function BUFUSBStopFrameGrab( ) : integer ; cdecl;
function BUFUSBShowFactoryControlPanel( deviceID : integer ; passWord: PChar ) : integer; cdecl;
function BUFUSBHideFactoryControlPanel() : integer; cdecl;
function BUFUSBGetFrameSetting( deviceID : integer ;
                                SettingPtr : PImageControl ) : integer; cdecl;
function BUFUSBSetFrameSetting( deviceID : THandle ;
                                SettingPtr : PImageControl ) : integer; cdecl;
function BUFUSBSetResolution( deviceID : integer ;
                              Resolution : integer; Bin : integer;
                              BufferCnt : integer ):integer; cdecl;
function BUFUSBSetCustomizedResolution( deviceID : integer ;
                                         RowSize : integer; ColSize : integer; Bin : integer;
                                         BufferCnt : integer ):integer; cdecl;
function BUFUSBSetExposureTime( deviceID : integer ; exposureTime : integer ) : integer; cdecl;
function BUFUSBSetFrameTime( deviceID : integer ; frameTime : integer ) : integer; cdecl;
function BUFUSBSetXYStart( deviceID : integer ;  XStart : integer; YStart : integer ):integer; cdecl;
function BUFUSBSetGains(deviceID : integer ;
                         RedGain : integer ; GreenGain : integer ; BlueGain : integer ):integer; cdecl;
function BUFUSBSetGainRatios(deviceID : integer ;
                             RedGainRatio : integer ; BlueGainRatio : integer ):integer; cdecl;
function BUFUSBSetGamma(Gamma : integer ; Contrast : integer ;
                         Bright: integer ; Sharp : integer ):integer;cdecl;
function BUFUSBSetBWMode(BWMode : integer ; H_Mirror : integer ; V_Flip : integer):integer;cdecl;
function BUFUSBInstallFrameHooker( FrameType : integer ; FrameHooker : TGetFrameCallBack  ) : integer; cdecl;
function BUFUSBInstallUSBDeviceHooker( USBDeviceHooker : TUSBDeviceCallBack ) : integer; cdecl;
function BUFUSBSetSoftTrigger( deviceID : THandle ) : integer; cdecl;
function BUFUSBSetCCDFrequency( deviceID : THandle ; Frequency : integer ) : integer; cdecl;
function BUFUSBSetUserMark( deviceID : THandle; UserMark : Byte ) : integer; cdecl;
function BUFUSBGetCurrentFrame( FrameType : integer; deviceID : THandle; var FrameBuf : PByte ) : PByte; cdecl; 
function BUFUSBSetGPIOConfig( deviceID : THandle ; ConfigByte : Byte ) : integer; cdecl;
function BUFUSBSetGPIOInOut( deviceID : integer ; OutputByte : Byte;
                             InputBytePtr : PByte ) : integer; cdecl;
function BUFUSBApplicationActivate( IsActive : Boolean ) : integer; cdecl;


implementation

function BUFUSBInitDevice; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_InitDevice';
function BUFUSBUnInitDevice; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_UnInitDevice';
function BUFUSBGetModuleNoSerialNo; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_GetModuleNoSerialNo';
function BUFUSBGetUserSerialNo; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_GetUserSerialNo';
function BUFUSBSetUserSerialNo; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetUserSerialNo';
function BUFUSBAddDeviceToWorkingSet; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_AddDeviceToWorkingSet';
function BUFUSBRemoveDeviceFromWorkingSet; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_RemoveDeviceFromWorkingSet';
function BUFUSBActivateDeviceInWorkingSet; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_ActiveDeviceInWorkingSet';
function BUFUSBStartCameraEngine; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_StartCameraEngine';
function BUFUSBStopCameraEngine; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_StopCameraEngine';
function BUFUSBSetBayerFilterType; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetBayerFilterType';
function BUFUSBSetCameraWorkMode; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetCameraWorkMode';
function BUFUSBStartFrameGrab; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_StartFrameGrab';
function BUFUSBStopFrameGrab; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_StopFrameGrab';
function BUFUSBShowFactoryControlPanel; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_ShowFactoryControlPanel';
function BUFUSBHideFactoryControlPanel; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_HideFactoryControlPanel';
function BUFUSBGetFrameSetting; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_GetFrameSetting';
function BUFUSBSetFrameSetting; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetFrameSetting';
function BUFUSBSetResolution; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetResolution';
function BUFUSBSetCustomizedResolution; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetCustomizedResolution';
function BUFUSBSetExposureTime; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetExposureTime';
function BUFUSBSetFrameTime; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetFrameTime';
function BUFUSBSetXYStart; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetXYStart';
function BUFUSBSetGains; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetGains';
function BUFUSBSetGainRatios; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetGainRatios';
function BUFUSBSetGamma; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetGamma';
function BUFUSBSetBWMode; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetBWMode';
function BUFUSBInstallFrameHooker; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_InstallFrameHooker';
function BUFUSBInstallUSBDeviceHooker; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_InstallUSBDeviceHooker';
function BUFUSBSetSoftTrigger; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetSoftTrigger';
function BUFUSBSetCCDFrequency; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetCCDFrequency';
function BUFUSBSetUserMark; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetUserMark';
function BUFUSBGetCurrentFrame; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_GetCurrentFrame';
function BUFUSBSetGPIOConfig; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetGPIOConfig';
function BUFUSBSetGPIOInOut; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_SetGPIOInOut';
function BUFUSBApplicationActivate; external 'BUF_USBCCDCamera_SDK.dll' name 'BUFCCDUSB_ApplicationActivate';


end.

