unit DataTypes;

interface

uses Windows, graphics;

const
  VID = $04B4;
  PID = $0428;  // For Bufferred Camera

  RAW_DATA_IMAGE = 0;
  BMP_DATA_IMAGE = 1;

  PRESET_SHOW_IMAGE_WIDTH = 480;
  PRESET_SHOW_IMAGE_HEIGHT= 360;

  FOREVER_TARGET_FRAMES = $8888;
  AUTO_EXPOSURE_ROI_WIDTH = 64;

  MAX_RESOLUTIONS = 10;
  MAX_RESOLUTIONS_M001 = 8;

  MAX_CAMERA_WORK_SET  = 8;
  MAX_EXPOSURE_TIME = 15000;   // (750*20); In 50us unit
  MIN_EXPOSURE_TIME = 1;

  MAX_EXPOSURE_TIME_LEVEL = 3;
  MAX_EXPOSURETIME : Array[0..MAX_EXPOSURE_TIME_LEVEL] of integer = ( 5, 10, 100, 750 );


  IMAGE_RESOLUTION : Array[1..MAX_RESOLUTIONS] of String =
        ( ' 64 x 64 ', ' 160 x 120 ', ' 320 x 240 ', ' 640 x 480 ', '752 x 480', ' 800 x 600 ',
          ' 1024 x 768 ', ' 1280 x 1024 ', ' 1600 x 1200 ', ' 2048 x 1536 ' );
  IMAGE_ROWS : Array[1..MAX_RESOLUTIONS] of integer =
        ( 64, 120, 240, 480, 480, 600, 768, 1024, 1200, 1536 );
  IMAGE_COLS : Array[1..MAX_RESOLUTIONS] of integer =
        ( 64, 160, 320, 640, 752, 800, 1024, 1280, 1600, 2048);

type
  eDEVICETYPE = ( MT9M001_M, MT9M001_C, MT9T001 );
  eWORKMODE = ( CONTINUE_MODE , EXT_TRIGGER_MODE );
  eAutoExposureState = ( FIRST_TIME_SET, FOLLOWING_SETS );
  //eEXTTRIGGERSTAT = ( EXT_SUCCESS, EXT_INPROCESS, EXT_ABORT );

  DWord = LongInt;
  PByte = ^Byte;
  PWord = ^Word;
  PDword = ^DWord;
  PLong = ^Integer;
  PInteger = ^Integer;
  pBitMap = ^TBitmap;

  LogPal = record
    lpal : TLogPalette;
    dummy:Array[0..255] of TPaletteEntry;
  end;  

  TImageSize = record
    Row : integer;
    Column : integer;
  end;

  TBUFCamera = record
    DeviceType : eDEVICETYPE;
    FWVersion  : integer;
    APVersion  : integer;
    BLVersion  : integer;
  end;

  TGrabFrameToFileCtl = record
    SavetoFileNeeded: Boolean;
    SaveAsJPEG : Boolean;
    AppendDataTime : Boolean;
    SwitchSkipModeNeeded : Boolean;
    SaveFileCount : integer;
    SavedCount: integer;
  end;

  TCameraControl = record
    CurrentMode  : eWORKMODE;
    Resolution : integer;
    Bin    : integer;
    ExposureTime : integer;
    XStart : integer;
    YStart : integer;
    RedGain: integer;
    GreenGain : integer;
    BlueGain : integer;

    AutoExposureEnable : integer;

    SaveFileCtl: TGrabFrameToFileCtl;
    GrabFrameCount : integer;
    GrabFrameDirectory : String;
    GrabFrameFile : String;

    IgnoreSkipMode : Boolean;
    SaveAsJpeg : Boolean;
    AppendDateTime : Boolean;
  end;

  TParameterSetCtl = record
    HaveCommand : Boolean;
    CommandValue: integer;
    ExtraValue1 : integer;
    ExtraValue2 : integer;
    ExtraValue3 : integer;
    ExtraValue4 : integer;
    Tag : integer;
    Command : ( SET_EXPOSURE, SET_XYSTART, SET_GAINS,
                SET_GAMMA, SET_GPIOCONFIG, SET_GPIOSET );
  end;

var
  OneInstaceMutex : THandle;
  ContinueRun : Boolean;
  CurrentDevices : integer;
  CurrentSelectedDevices : integer;
  SelectedDevice : integer;
  CurrentDeviceIndex : integer;
  GrabFrameType : integer;

  GlobalParaSetCtl : TParameterSetCtl;
  //ParaSetCtl : TParameterSetCtl;
  //SaveFileCtl: TGrabFrameToFileCtl;

  CameraModuleNo: Array[1..MAX_CAMERA_WORK_SET] of String;
  CameraSerialNo: Array[1..MAX_CAMERA_WORK_SET] of String;
  //CameraParaControl : Array[1..MAX_CAMERA_WORK_SET] of TCameraControl;
  CameraSelected : Array[1..MAX_CAMERA_WORK_SET] of Boolean;
  SelectableDevices : Array[0..MAX_CAMERA_WORK_SET-1] of integer;
  
implementation

end.
