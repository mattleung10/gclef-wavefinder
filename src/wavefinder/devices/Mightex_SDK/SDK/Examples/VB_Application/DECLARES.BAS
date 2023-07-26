Attribute VB_Name = "Module1"
Option Explicit
'Dim WinVersion As Integer, SoundAvailable As Integer
'Public VisibleFrame As Frame
Dim FrameCount As Long
Dim ImageBuf() As Byte
 
Public Const RAWDATA_IMAGE = 0
Public Const BMPDATA_IMAGE = 1
Public Const NORMAL_MODE = 0
Public Const TRIGGER_MODE = 1
Public Const GRAB_FRAME_FOREVER = &H8888


Public Type TPROCESSEDDATAPROPERTY
    CameraID As Long
    Row As Long
    Column As Long
    Bin As Long
    XStart As Long
    YStart As Long
    exposureTime As Long
    RedGain As Long
    GreenGain As Long
    BlueGain As Long
    TimeStamp As Long
    TriggerOccurred As Long
    TriggerEventCount As Long
    UserMark As Long
    FrameTime As Long
    CCDFrequency As Long
    ProcessFrameType As Long
    tFilterAcceptForFile As Long
End Type


Declare Function BUFCCDUSB_InitDevice Lib "BUF_USBCCDCamera_SDK_Stdcall" () As Long
Declare Function BUFCCDUSB_UnInitDevice Lib "BUF_USBCCDCamera_SDK_Stdcall" () As Long
Declare Function BUFCCDUSB_GetModuleNoSerialNo Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal ModuleNo As String, ByVal SerialNo As String) As Long
Declare Function BUFCCDUSB_AddDeviceToWorkingSet Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long) As Long
Declare Function BUFCCDUSB_RemoveDeviceFromWorkingSet Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long) As Long
Declare Function BUFCCDUSB_StartCameraEngine Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal ParentHandle As Long, ByVal CameraBitOption As Long) As Long
Declare Function BUFCCDUSB_StopCameraEngine Lib "BUF_USBCCDCamera_SDK_Stdcall" () As Long
Declare Function BUFCCDUSB_SetCameraWorkMode Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal WorkMode As Long) As Long
' The following two APIs are not recommended...we recommend user to install frame callback for NORMAL and TRIGGER modes
'Declare Function MTUSB_SetExternalParameters Lib "MT_USBCCDCamera_SDK_Stdcall" ( ByVal DevHandle As Long, ByVal AutoLoop As Byte, ByVal IsRawGraph as Byte, ByVal IsJPEG As Byte, ByVal FilePath as String, ByVal FileName As String) as long
'Declare Function MTUSB_WaitingExternalTrigger Lib "MT_USBCCDCamera_SDK_Stdcall" ( DEV_HANDLE DevHandle, bool StartWait, CallBackFunc Aproc );
Declare Function BUFCCDUSB_ShowFactoryControlPanel Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal passWord As String) As Long
Declare Function BUFCCDUSB_HideFactoryControlPanel Lib "BUF_USBCCDCamera_SDK_Stdcall" () As Long
Declare Function BUFCCDUSB_StartFrameGrab Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal TotalFrames As Long) As Long
Declare Function BUFCCDUSB_StopFrameGrab Lib "BUF_USBCCDCamera_SDK_Stdcall" () As Long
Declare Function BUFCCDUSB_SetCustomizedResolution Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal RowSize As Long, _
                                                                                  ByVal ColSize As Long, ByVal Bin As Long, ByVal BufferCnt As Long) As Long
Declare Function BUFCCDUSB_SetExposureTime Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal exposureTime As Long) As Long
Declare Function BUFCCDUSB_SetXYStart Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal XStart As Long, ByVal YStart As Long) As Long
Declare Function BUFCCDUSB_SetGains Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal RedGain As Long, ByVal GreenGain As Long, _
                                                                   ByVal BlueGain As Long) As Long
Declare Function BUFCCDUSB_SetGamma Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal Gamma As Long, ByVal Contrast As Long, ByVal Bright As Long, ByVal Sharp As Long) As Long
Declare Function BUFCCDUSB_SetBWMode Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal BWMode As Long, ByVal H_Mirror As Long, ByVal V_Flip As Long) As Long
Declare Function BUFCCDUSB_InstallFrameHooker Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal FrameType As Long, ByVal FrameHooker As Long) As Long
Declare Function BUFCCDUSB_InstallUSBDeviceHooker Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal USBDeviceHooker As Long) As Long
Declare Function BUFCCDUSB_SetGPIOConifg Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal ConfigByte As Byte) As Long
Declare Function BUFCCDUSB_SetGPIOInOut Lib "BUF_USBCCDCamera_SDK_Stdcall" (ByVal deviceID As Long, ByVal OutputByte As Byte, ByRef InputByteState As Byte) As Long
                                                                                  
Declare Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (Destination As Any, Source As Any, ByVal Length As Long)
'

Sub MyFrameHooker(ByRef lpImageAttribute As TPROCESSEDDATAPROPERTY, ByRef Buffer As Byte)
    Dim MyStr As String
    Dim i As Long
    Dim TotalPixel As Long
    Dim Average As Long, Row As Long, Column As Long, Bin As Long
    

    Row = lpImageAttribute.Row
    Column = lpImageAttribute.Column
    FrameCount = FrameCount + 1
    ReDim ImageBuf(Column * Row)
       
    ' We copy the image data to ImageBuf()...Note that this callback is invoked in a higher
    ' priority thread... so this callback should not be blocked or do any GUI operations
    ' (Although this example does a simple GUI showing for demo purpose)...we recommend user to put the
    ' Image data and attributes in buffer and post a message to main thread for further
    ' processing.
    CopyMemory ImageBuf(0), Buffer, (Column * Row)
    TotalPixel = 0
    For i = 0 To (Column * Row - 1)
        TotalPixel = TotalPixel + ImageBuf(i)
    Next
    Average = TotalPixel / (Column * Row)
        
    MyStr = "Frames: " & FrameCount & "   Resolution: " & Column & "x" & Row & " Gain (" & lpImageAttribute.RedGain _
     & "," & lpImageAttribute.GreenGain & "," & lpImageAttribute.BlueGain & ") PixelValue: " & Average
    Form1.StatusLabel.Caption = MyStr
    
End Sub
