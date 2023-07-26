unit BUFCamera_Example;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, RzCmboBx, RzStatus, RzSplit, RzPanel, ExtCtrls, RzRadGrp,
  TeEngine, Series, TeeProcs, Chart, DataTypes, DllInterface, RzButton,
  Mask, RzEdit, RzTrkBar, RzLabel, ImgList, RzShellDialogs, inifiles,
  RzRadChk, Buttons, ComCtrls;

const
  WM_USER_NOTIFY = WM_USER + 100;

  MAX_BUF_POINTS = 3648;
  BUF_POINT_START = 32;

  MAX_FRAME_NUM = 3;
  IMAGE_ROWS_ICX205 : Array[0..MAX_FRAME_NUM] of integer = ( 256, 344, 520, 1040 );
  IMAGE_COLS_ICX205 : Array[0..MAX_FRAME_NUM] of integer = ( 348, 464, 696, 1392 );
  IMAGE_BIN_ICX205  : Array[0..MAX_FRAME_NUM] of integer = (  $83, $82, $81, 0 );

  // This sample code takes CCX camera as example, for CGX camera, we might have the
  // following definitions:
  {
  IMAGE_ROWS_ICX445 : Array[0..MAX_FRAME_NUM] of integer = ( 240, 320, 480, 960 );
  IMAGE_COLS_ICX445 : Array[0..MAX_FRAME_NUM] of integer = ( 320, 424, 640, 1280 );
  IMAGE_BIN_ICX445  : Array[0..MAX_FRAME_NUM] of integer = (  $83, $82, $81, 0 );
  }
type
  TMainForm = class(TForm)
    RzPanel1: TRzPanel;
    RzPanel2: TRzPanel;
    DevicesComboBox: TComboBox;
    ReSelectDeviceBitBtn: TBitBtn;
    ShowFactoryPanelBitBtn: TBitBtn;
    ShowImageButton: TBitBtn;
    StatusBar1: TStatusBar;
    SetToNormalModeButton: TButton;
    SetToTriggerModeButton: TButton;
    SetExposureTimeButton: TButton;
    ExposureTimeEdit: TEdit;
    Label1: TLabel;
    ResolutionComboBox: TComboBox;
    XStartEdit: TEdit;
    YStartEdit: TEdit;
    Label2: TLabel;
    Label3: TLabel;
    SetXYStartButton: TButton;
    RedGainEdit: TEdit;
    GreenGainEdit: TEdit;
    BlueGainEdit: TEdit;
    Label4: TLabel;
    Label5: TLabel;
    Label6: TLabel;
    SetGainButton: TButton;
    SetResolutionButton: TButton;
    Button1: TButton;
    GetCurrentFrameButton: TButton;
    procedure FormShow(Sender: TObject);
    procedure DevicesComboBoxChange(Sender: TObject);
    procedure ShowFactoryPanelBitBtnClick(Sender: TObject);
    procedure ShowImageButtonClick(Sender: TObject);
    procedure FormClose(Sender: TObject; var Action: TCloseAction);
    procedure ReSelectDeviceBitBtnClick(Sender: TObject);
    procedure SetToNormalModeButtonClick(Sender: TObject);
    procedure SetToTriggerModeButtonClick(Sender: TObject);
    procedure SetExposureTimeButtonClick(Sender: TObject);
    procedure SetResolutionButtonClick(Sender: TObject);
    procedure SetXYStartButtonClick(Sender: TObject);
    procedure SetGainButtonClick(Sender: TObject);
    procedure Button1Click(Sender: TObject);
    procedure GetCurrentFrameButtonClick(Sender: TObject);
    //procedure GetUserSerialNoButtonClick(Sender: TObject);
    //procedure SetUserSerialNoButtonClick(Sender: TObject);
  private
    { Private declarations }

    procedure DeviceReInitializeNeededMsg( var Msg : TMessage ); message WM_USER_NOTIFY;
  public
    { Public declarations }
  end;

var
  MainForm: TMainForm;
  ImageCount : integer;
  DebugBuffer : Array [0..$400000] of Byte;
  RepeatRecord: Array[0..$10000] of integer;
  startTimeTick, endTimeTick : integer;
  frameRate : integer;
  CurrentWorkingMode : integer;
  CurrentFrameDataArray : Array of Byte;

implementation

{$R *.DFM}

uses DeviceSelect;

procedure DeviceFaultCallBack( DevieType: integer ); cdecl;
begin
  {
    JTZ: DeviceFaultCallBack is invoked by camera engine while the device mapping is
    changed ( device plug/unplug ) OR device error occurred. In this case, the camera
    engine invokes this hooker, the engine will do the following before invoke tha
    callback:
    1). Internally, engine stops to grab frames from any device
    2). Engine will unhook this hooker...so this is a "One-Shot" hooker.
    In this case, camera engine is in "Sleep" state and can only be woke up by
    re-initialization of the devices.
    So application is supposed to do the following:
    1). Post a message for further operations, it's NOT recommended to do
    cleaning and re-initialization in this callback.
    2). In the message handler, it should do all the house keeping as following:
       BUFUSBInstallFrameHooker( 0, nil);
       BUFUSBInstallUSBDeviceHooker( nil);
       BUFUSBStopCameraEngine();
       BUFUSBUnInitDevice();
    3). And then, it's supposed to do ( User may also show a warning and close
        application):
       BUFUSBInitDevice();
       ...
  }
  PostMessage( MainForm.Handle, WM_USER_NOTIFY, 0 , 0 );
end;

procedure FrameCallBack( ImageProperty : PProcessedDataProperty; Buffer : PByte ); cdecl;
var
  i : integer;
  Row, Column, FrameSize : integer;
  SPtr : PByte;
  RepeatCnt : integer;
  LastByte : Byte;
  TimeEllapse : integer;
begin
  {
    JTZ: For Linear camera, the callback is invoked in PanelFrom.Timer..which is in the
    main thread..so we're free to do any UI operations. Blocking the callback may pause
    the camera engine for a little while...the result is lower frame rate.
  }
  {
    In this sample code, we only process the frame from the current selected Device, note that
    camera engine will invoke frame callback for each Frame from any camera which was added
    in working set. In case of multiple cameras are used, the ImageProperty.CameraID is
    the identity of the camera (it's the same number userd for calling BUFUSBAddDeviceToWorkingSet()
  }
  if ImageProperty.CameraID = SelectedDevice then // This is the Data flow from current camera.
    begin
      Inc( ImageCount );
      if ImageCount = 1 then
        startTimeTick := ImageProperty.TimeStamp;
      if (ImageCount mod 10) = 0 then
        begin
          ImageCount := 0;
          endTimeTick := ImageProperty.TimeStamp;
          if endTimeTick < startTimeTick then
            TimeEllapse := endTimeTick + $10000 - startTimeTick
          else
            TimeEllapse := endTimeTick - startTimeTick;
          frameRate := 10000 div TimeEllapse;
      //FrameRatePane.Caption := IntToStr(frameRate) + 'fps';
      MainForm.StatusBar1.Panels[2].Text := IntToStr(frameRate) + 'fps';

      //MainForm.StatusBar1.Panels[2].Text := IntToStr( ImageProperty.CameraID );
      { ImageProperty.ExposureTime has the Exposure time for this frame }
      MainForm.StatusBar1.Panels[3].Text := IntToStr( ImageProperty.ExposureTime * 50 ) + ' us';
      { ImageProperty.TimeStamp has the TimeStamp (in 1ms unit) for this frame, note this
        is a 0 -- 65535 and round back number }
      MainForm.StatusBar1.Panels[4].Text := IntToStr( ImageProperty.TimeStamp );
      { ImageProperty.TriggerOccurred is mainly for NORMAL mode, while camera is in NORMAL
        mode, camera is still monitoring the TRIGGER signal and if it's asserted, the
        current frame will be marked with TriggerOccurred to be "1", otherwise it's "0",
        This gives application an alternative to poll the TRIGGER signal in NORMAL mode.
      }
      MainForm.StatusBar1.Panels[5].Text := IntToStr( ImageProperty.TriggerOccurred);
      {
        ImageProperty.TriggerEventCount is used for TRIGGER mode only, it's always "0" in
        NORMAL mode. While in TRIGGER mode, there might be multiple trigger signals (edges
        on Trigger Hardware Pin), each signal will increase this count by "1", and it's reset
        to "0" by application when setting the mode to "TRIGGER". (Note that application might
        set the mode to "TRIGGER" explicitly even when the current mode was already "TRIGGER",
        this setting is actually used for reset the count only).
        One thing worth to mention is that: Each frame takes 1ms -- hundreds of ms, so if there's
        more than ONE signals in the frame time...the TriggerEventCount for frames might NOT
        be continuous from frame to frame, e.g. for this Frame, the count is 1, and next frame
        the count might be 8. (In this case, there're 7 triggers occurred in the first frame time)
        In application, it's system integrator's responsibility to design the external trigger
        machenism properly.
      }
      MainForm.StatusBar1.Panels[6].Text := IntToStr( ImageProperty.TriggerEventCount);
      {
        ImageProperty.ProcessFrameType is the Frame data type, it's the same as the "FrameType"
        In BUFUSBInstallFrameHooker( FrameType : integer...), it can be "RAW_DATA" or "BMP_DATA".
      }
      MainForm.StatusBar1.Panels[7].Text := IntToStr( ImageProperty.ProcessFrameType);
        end;
      if CurrentWorkingMode = 1 then  //Trigger mode
        MainForm.StatusBar1.Panels[4].Text := IntToStr( ImageProperty.TimeStamp );
      {
        For other items in ImageProperty, they're
          Row          : integer;
          Column       : integer;
          Bin          : integer;
          XStart       : integer;
          YStart       : integer;
          RedGain      : integer;
          GreenGain    : integer;
          BlueGain     : integer;

          We won't show them on window, as they're pretty much "straight forward".
      }
      Row := ImageProperty.Row;
      Column := ImageProperty.Column;
      if ImageProperty.ProcessFrameType = 0 then // RAW_DATA
        begin
          FrameSize := Row * Column;
          if Is8BitCamera = False then
            FrameSize := FrameSize * 2; // 10bit camera.
          SPtr := Buffer;
          //LastByte := $0;
          //RepeatCnt := 0;
          for i:=0 to FrameSize-1 do
            begin
              DebugBuffer[i] := SPtr^;
              {
              if SPtr^ = LastByte then
                begin
                  RepeatRecord[RepeatCnt] := i;
                  Inc(RepeatCnt);
                end;
              LastByte := SPtr^;
              }
              Inc( SPtr );
            end;
          //MainForm.StatusBar1.Panels[2].Text := IntToStr( RepeatCnt );
        end
      else  // BMP_DATA
        begin
          if Pos( 'B0', CameraModuleNo[ImageProperty.CameraID] ) <> 0 then  // It's Mono Camera
            FrameSize := Row * Column  { it's 8bit BITMAP, same as the RAW_DATA}
          else
            FrameSize := Row * Column * 3; { it's 24bit BITMAP }
          SPtr := Buffer;
          for i:=0 to FrameSize-1 do
            begin
              DebugBuffer[i] := SPtr^;
              Inc( SPtr );
            end;
        end;
       {
          We can get "FrameSize" data from the Buffer, note that data is in
          BYTES[ROW,COLUMN] format.
       }
    end;
end;

procedure TMainForm.DeviceReInitializeNeededMsg( var Msg : TMessage );
begin
  if TMessage(Msg).Msg = WM_USER_NOTIFY then
    begin
      // In this sample code, the "ReselectDevice" Button will do all the works
      // this message handler is supposed to do.
      ReSelectDeviceBitBtnClick( Self );
    end;
end;


procedure TMainForm.FormShow(Sender: TObject);
var
  device : integer;
  i : integer;
begin
  i:=0;
  for device :=1 to CurrentDevices do
    begin
      {
        Note that CurrentDevices is the number of current connected BUF Camera
        Devices, but not all the them might be selected as "Working" camera,
        for example, we might have 5 BUF cameras connected on USB, but only
        2 and 4 are selected, in this case, we have:
        CameraSelected[] = (0, 1, 0, 1, 0);   2 and 4 are selected.
        Note that 2 and 4 are also the CameraID returned in the frame callback.
      }
      if CameraSelected[device] then
        begin
          BUFUSBAddDeviceToWorkingSet( device );
          DevicesComboBox.Items.Add( CameraSerialNo[device] );
          // The purpose of SelectableDevices is for quick getting of the
          // SelectedDevice ( SelectableDevices[DevicesComboBox.ItemIndex] )
          // Here the SelectedDevices is "1" based SELECTED device no.
          SelectableDevices[i] := device;
          Inc(i);
        end;
    end;
  // Let's install two callbacks here.
  BUFUSBInstallFrameHooker( 0, FrameCallBack );  // RAW data.
  BUFUSBInstallUSBDeviceHooker( DeviceFaultCallBack );
  if Is8BitCamera = True then
    BUFUSBStartCameraEngine( Handle, 8 )
  else
    BUFUSBStartCameraEngine( Handle, 10);
  DevicesComboBox.ItemIndex := 0;
  ResolutionComboBox.ItemIndex := 3;
  SelectedDevice := SelectableDevices[DevicesComboBox.ItemIndex];

  StatusBar1.Panels[0].Text := 'Selected: ' + IntToStr(CurrentSelectedDevices)
                               + ' Cameras';
  StatusBar1.Panels[1].Text := CameraModuleNo[SelectedDevice] + ':' +
                               CameraSerialNo[SelectedDevice];
  ShowImageButton.Caption := 'Start Grab';
  CurrentWorkingMode := 0;

  // For testing GetCurrentFrame
  SetLength( CurrentFrameDataArray, 10000 ); // For first 10000 bytes only.
end;

procedure TMainForm.DevicesComboBoxChange(Sender: TObject);
begin
  SelectedDevice := SelectableDevices[DevicesComboBox.ItemIndex];
  StatusBar1.Panels[1].Text := CameraModuleNo[SelectedDevice] + ':' +
                               CameraSerialNo[SelectedDevice];
end;



procedure TMainForm.ShowFactoryPanelBitBtnClick(Sender: TObject);
begin
  BUFUSBShowFactoryControlPanel( SelectedDevice, '661016' );
end;

procedure TMainForm.ShowImageButtonClick(Sender: TObject);
begin
  // Start or Stop Frame Grabbing.
  if ShowImageButton.Caption = 'Start Grab' then
    begin
      // Start the grabbing
      ShowImageButton.Caption := 'Stop Grab'; // Show "STOP" icon
      BUFUSBStartFrameGrab( FOREVER_TARGET_FRAMES );   // Get 10000 Frames only.
    end
  else // "STOP" icon is showing.
    begin
      // Stop the grabbing
      ShowImageButton.Caption := 'Start Grab'; // Show "START" icon.
      BUFUSBStopFrameGrab();
    end;
end;

procedure TMainForm.FormClose(Sender: TObject; var Action: TCloseAction);
begin
  // When user exit the application.
  BUFUSBStopCameraEngine();
  BUFUSBUnInitDevice();
  SetLength( CurrentFrameDataArray, 0 );
end;

procedure TMainForm.ReSelectDeviceBitBtnClick(Sender: TObject);
var
  DevideForm : TDeviceForm;
begin
  // 1. House Keeping.
  BUFUSBInstallFrameHooker( 0, nil);
  BUFUSBInstallUSBDeviceHooker( nil);
  BUFUSBStopCameraEngine();
  BUFUSBUnInitDevice();
  DevicesComboBox.Items.Clear;
  DevicesComboBox.ItemIndex := -1;
  
  // 2. Show Device Selection Form again
  DeviceForm := TDeviceForm.Create( Application );
  DeviceForm.ShowModal;
  DeviceForm.Free;

  // 3. Explicitly call FormShow();
  // In FormShow(), it will install hookers and start the camera engine.
  FormShow( Self );
end;

procedure TMainForm.SetToNormalModeButtonClick(Sender: TObject);
begin
    //BUFUSBSetCameraWorkMode( SelectedDevice, 1 );
    CurrentWorkingMode := 0;
    BUFUSBSetCameraWorkMode( SelectedDevice, 0 );
end;

procedure TMainForm.SetToTriggerModeButtonClick(Sender: TObject);
begin
  CurrentWorkingMode := 1;
  BUFUSBSetCameraWorkMode( SelectedDevice, 1 );
end;

procedure TMainForm.SetExposureTimeButtonClick(Sender: TObject);
var
  ExposureTime : integer;
begin
  ExposureTime := StrToInt( ExposureTimeEdit.Text );
  ExposureTime := ExposureTime div 50; // in 50us unit.
  BUFUSBSetExposureTime( SelectedDevice, ExposureTime );
end;

procedure TMainForm.SetResolutionButtonClick(Sender: TObject);
var
  currentResolution : integer;
  Bin : integer;
begin
  currentResolution := ResolutionComboBox.ItemIndex;
  BUFUSBSetCustomizedResolution( SelectedDevice, IMAGE_COLS_ICX205[MAX_FRAME_NUM],
     IMAGE_ROWS_ICX205[currentResolution], IMAGE_BIN_ICX205[currentResolution], 4 );
end;

procedure TMainForm.SetXYStartButtonClick(Sender: TObject);
var
  XStart, YStart : integer;
begin
  XStart := StrToInt( XStartEdit.Text );
  YStart := StrToInt( YStartEdit.Text );
  BUFUSBSetXYStart( SelectedDevice, XStart, YStart );
end;

procedure TMainForm.SetGainButtonClick(Sender: TObject);
var
  RGain, GGain, BGain : integer;
begin
  RGain := StrToInt( RedGainEdit.Text );
  GGain := StrToInt( GreenGainEdit.Text );
  BGain := StrToInt( BlueGainEdit.Text );
  BUFUSBSetGains( SelectedDevice, RGain, GGain, BGain );
end;


procedure TMainForm.Button1Click(Sender: TObject);
var
  device : integer;
begin
  CurrentWorkingMode := 1; // showing TimeStamp for each frame. 
  BUFUSBActivateDeviceInWorkingSet( SelectedDevice, 1 );
  for device :=0 to MAX_CAMERA_WORK_SET-1 do
    begin
      if ( SelectableDevices[device] > 0 ) AND
         ( SelectableDevices[device] <> SelectedDevice ) then
        BUFUSBActivateDeviceInWorkingSet( SelectableDevices[device], 0 );
    end;
  BUFUSBSetCameraWorkMode( SelectedDevice, 0 );
  BUFUSBStartFrameGrab(1);
end;

procedure TMainForm.GetCurrentFrameButtonClick(Sender: TObject);
var
  sPtr , rPtr : PByte;
  i : integer;
begin
  // Uninstall the frame hooker.
  BUFUSBInstallFrameHooker( 0, nil );
  rPtr := BUFUSBGetCurrentFrame( 0, SelectedDevice, sPtr );
  if rPtr <> nil then
    begin
      for i:=0 to 9999 do
        begin
          CurrentFrameDataArray[i] := sPtr^;
          Inc( sPtr );
        end;
    end
  else
    begin
      ShowMessage( 'GetCurrentFrame Time Out!' );
    end;
end;

{
procedure TMainForm.GetUserSerialNoButtonClick(Sender: TObject);
var
  UserSerialNo : Array[0..15] of Char;
begin
  BUFUSBStopCameraEngine();
  // Get User Serial No.
  BUFUSBGetUserSerialNo( SelectedDevice, UserSerialNo );
  UserSerialNo[13] := #0;
  UserSerialNoEdit.Text := String(UserSerialNo);
end;

procedure TMainForm.SetUserSerialNoButtonClick(Sender: TObject);
var
  i, len : integer;
  UserSerialNo : Array[0..15] of Char;
  UserStr : String;
begin
  // Get User Serial No.
  for i:=0 to 15 do
    UserSerialNo[i] := #0;
  UserStr := UserSerialNoEdit.Text;
  len := Length(UserStr );
  for i:=1 to len do
    begin
      UserSerialNo[i-1] := Char( UserStr[i] );
    end;
  BUFUSBSetUserSerialNo( SelectedDevice, UserSerialNo, 1 );
end;
}
end.
