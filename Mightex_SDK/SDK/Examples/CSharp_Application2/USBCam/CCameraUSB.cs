using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using System.Diagnostics;
using System.Xml;
using System.Xml.Serialization;

namespace USBCam
{
    [StructLayout(LayoutKind.Explicit)]
    public struct ImageProperty
    {
        [FieldOffset(0)] public int CameraID;
        [FieldOffset(4)] public int Row;
        [FieldOffset(8)] public int Column;
        [FieldOffset(12)] public int Bin;
        [FieldOffset(16)] public int XStart;
        [FieldOffset(20)] public int YStart;
        [FieldOffset(24)] public int ExposureTime;
        [FieldOffset(28)] public int RedGain;
        [FieldOffset(32)] public int GreenGain;
        [FieldOffset(36)] public int BlueGain;
        [FieldOffset(40)] public int TimeStamp;
        [FieldOffset(44)] public int TriggerOccurred;
        [FieldOffset(48)] public int TriggerEventCount;
        [FieldOffset(52)] public int UserMark;
        [FieldOffset(56)] public int FrameTime;
        [FieldOffset(60)] public int CCDFrequency;
        [FieldOffset(64)] public int ProcessFrameType;
        [FieldOffset(68)] public int tFilterAcceptForFile;
    }

    public delegate void FrameCallbackDelegate( ref ImageProperty frameProperty, IntPtr BufferPtr );

    public class CCameraUSB
    {
        //Members...
        public enum IMAGES {RAW, BMP, JPG};
        public enum CAM_WORKMODE {VIDEO, EXT_TRIG};
        public enum FRAME_TYPE { RAW, DIB };
        public enum SHARPNESS_LEV { NORMAL, SHARP, SHARPER, SHARPEST };
        public enum RESOLUTION { TINY, LITTLE, SMALL, NORMAL }
        public enum CAMERA_BIT { BIT_8_CAMERA = 8, BIT_12_CAMERA = 12 };
        public const int INFINITE_FRAMES = 0x8888;
        public FrameCallbackDelegate frameDelegate;
        private FUSBCam MightexCam; // The GUI class
        private int _deviceID = 1;
        private string _camError = "USB Camera Error";
        private IntPtr _pImage = new IntPtr();  //image pointer

        private int _maxX;
        public int MaxX
        {
            get { return _maxX; }
        }
        private int _maxY;
        public int MaxY
        {
            get { return _maxY; }
        }

        private int pixelDepthBits = 24/8;  //24 bit color camera div by 8 bits for 3 bytes total
        public int PixelDepth
        {
            get { return pixelDepthBits; }
        }

        public struct ImageControl
        {
            [XmlElement("Revision")]
            public RESOLUTION _resolution;
            public int _rowSize;
            public int _columnSize;
            public int _binMode;        //1 ?No Skip mode, 2 ?2X skip(1:2 decimation)
            public int _xStart;        //Upper left hand corner, positive right 
            public int _yStart;        //Upper left hand corner, positive down
            public int _greenGain;     //Green Gain Value: 0 ?128, the actual gain is GreenGain/8
            public int _blueGain;      //Blue Gain Value: 0 ?128, the actual gain is BlueGain/8
            public int _redGain;       //Red Gain Value: 0 ?128, the actual gain is RedGain/8
            public int _exposureTime;  //current exposure time in microseconds

            public int _gamma;         //Gamma value: 0 ?20, means 0.0 ?2.0
            public int _contrast;      //Contrast value: 0 ?100, means 0% -- 100%
            public int _bright;        //Brightness : 0 ?100, means 0% -- 100%

            public int  _sharpLevel;   //SharpLevel index: 0=Normal, 1=Sharp, 2=Sharper, 3=Sharpest
            public int _blkWhtMode;   //true for B&W
            public int _horzMirror;   //true for Horiz
            public int _vertFlip;     //true for vertical flip
        }

        private ImageControl _imgControl = new ImageControl();

        //default constructor for testing
        public CCameraUSB( FUSBCam mightexCamera )
        {
            _imgControl._resolution = RESOLUTION.NORMAL;
            _imgControl._rowSize = 1392;    // Note: we take CCX as example, for other modules, please
            _imgControl._columnSize = 1040; // refer to SDK manual for correct rowSize/columnSize.
            _imgControl._binMode = 0;
            _imgControl._xStart = 0;
            _imgControl._yStart = 0;
            _imgControl._greenGain = 14;
            _imgControl._blueGain = 14;
            _imgControl._redGain = 14;
            _imgControl._exposureTime = 5000; // 5ms.

            _imgControl._gamma = 10;
            _imgControl._contrast = 50;
            _imgControl._bright = 50;

            _imgControl._sharpLevel = 0;
            _imgControl._blkWhtMode = 0;
            _imgControl._horzMirror = 0;
            _imgControl._vertFlip = 0;

            MightexCam = mightexCamera;
            frameDelegate = new FrameCallbackDelegate(GrabbingFrameCallback);
            _maxX = 1280; // Assume we're using 1.3M camera.
            _maxY = 1024; 
        }

        // JTZ: The frame callback.
        public void GrabbingFrameCallback(  ref ImageProperty frameProperty, IntPtr BufferPtr)
        {
            uint i, pixelAvg;
            uint frameSize;

            unsafe
            {
                byte *frameptr;

                /*
                 * JTZ: In tihs example, we get "Raw" data.
                 */
                pixelAvg = 0;
                frameSize = (uint)(frameProperty.Row * frameProperty.Column * 3) ;
                frameptr = (byte *)BufferPtr;
                for ( i=0; i<frameSize; i++ )
                {
                    pixelAvg += *frameptr;
                    frameptr++;
                }
                pixelAvg = pixelAvg / frameSize;
            }
            
            /*
             * JTZ: For Buffer camera, the callback in invoked in the main thread of the application, so it's 
             * allowed to do any GUI operations here...however, don't block here.
             */
            MightexCam.SetCallBackMessage(ref frameProperty, pixelAvg, BufferPtr);
        }

        public int GetExpTime()
        {
            return _imgControl._exposureTime;
        }

        public int GetXstart()
        {
            return _imgControl._xStart;
        }
        public int GetYstart()
        {
            return _imgControl._yStart;
        }

        public int GetRedGain()
        {
            return _imgControl._redGain;
        }
        public int GetGreenGain()
        {
            return _imgControl._greenGain;
        }
        public int GetBlueGain()
        {
            return _imgControl._blueGain;
        }

        public bool GetBlkWht()
        {
            return (_imgControl._blkWhtMode == 1 ? true : false);
        }
        public bool GetHorzMirr()
        {
            return (_imgControl._horzMirror == 1 ? true : false);
        }
        public bool GetFlipVert()
        {
            return (_imgControl._vertFlip == 1 ? true : false);
        }
        public void SetHorzMirr(bool HorzMirr)
        {
            if (HorzMirr)
                _imgControl._horzMirror = 1;
            else
                _imgControl._horzMirror = 0;
        }
        public void SetFlipVert(bool FlipVert)
        {
            if (FlipVert)
                _imgControl._vertFlip = 1;
            else
                _imgControl._vertFlip = 0;
        }
        //Thin wrapper for calling into BUF_USBCCDCamera_SDK_Stdcall.dll
        //Interops are in the USBCam.Designer.cs (partial class) file

        /// <summary>
        /// Call this function first, this function communicates with device driver to reserve resources
        /// </summary>
        /// <returns>number of cameras on USB 2.0 chan</returns>
        public int InitDevice()
        {
            int numCam = BufInitDevice();

            if ( numCam < 0 )
            {
                MessageBox.Show("Error trying to initialize camera resources. No cameras found on USB 2.0 bus.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            return numCam;
        }
        
        //Call this function before the app terminates, it releases all resources
        public void UnInitDevice()
        {
            if (BufUnInitDevice() < 0)
            {
                MessageBox.Show("Error trying to uninitialize camera.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Function used to get the module number on a particular USB channel
        /// </summary>
        /// <returns></returns>
        public string GetModuleNo()
        {
            string moduleNumber = "Unknown";
            //char moduleNo = 'X';
            StringBuilder rtnModuleNo = new StringBuilder();
            StringBuilder rtnSerialNo = new StringBuilder();

            if (BufGetModuleNoSerialNo( _deviceID, rtnModuleNo, rtnSerialNo) < 0)
            {
                MessageBox.Show("Error trying to retrieve camera module number.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
            {
                moduleNumber = rtnModuleNo.ToString();
            }
            return moduleNumber;
        }

        /// <summary>
        /// Function used to get the serial number on a particular USB channel
        /// </summary>
        /// <returns></returns>
        public string GetSerialNo()
        {
            string serialNumber = "Unknown2";
            StringBuilder rtnModuleNo = new StringBuilder();
            StringBuilder rtnSerialNo = new StringBuilder();

            if (BufGetModuleNoSerialNo(_deviceID, rtnModuleNo, rtnSerialNo) < 0)
            {
                MessageBox.Show("Error trying to retrieve camera serial number.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
            {
                serialNumber = rtnSerialNo.ToString();
            }
            return serialNumber;
        }

        public void AddCameraToWorkingSet(int cameraID)
        {
            _deviceID = cameraID;
            if (BufAddDeviceToWorkingSet( cameraID ) < 0)
            {
                MessageBox.Show("Error adding camera to working set", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

        }

        public void RemoveCameraFromWorkingSet(int cameraID)
        {
            if (BufRemoveDeviceFromWorkingSet(cameraID) < 0)
            {
                MessageBox.Show("Error removing camera from working set", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

        }


        //Camera has multithread engine internally, which is responsible for all the frame grabbing, raw data to RGB data conversion…etc. functions. 
        //User MUST start this engine for all the following camera related operations
        //ParentHandle ?The window handle of the main form of user’s application, as the engine relies on
        //Windows Message Queue, it needs a parent window handle
        public void StartCameraEngine(IntPtr parentHandle)
        {
            if (BufStartCameraEngine(parentHandle, (uint)CAMERA_BIT.BIT_8_CAMERA) < 0)
            {
                MessageBox.Show("Error trying to start camera engine.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Stops the started camera engine.
        /// </summary>
        public void StopCameraEngine()
        {
            if ( BufStopCameraEngine() < 0 )
            {
                MessageBox.Show("Error trying to stop camera engine.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Sets camera to either "video" mode - continuously deliver frames to PC or
        /// "external trigger" mode - camera waits for external trigger to capture 1 frame
        /// </summary>
        /// <param name="mode"></param>
        public void SetCameraWorkMode(CAM_WORKMODE mode)
        {
            int WorkMode = (int)mode;
            if (BufSetCameraWorkMode(_deviceID, WorkMode) < 0) // We take the first camera as example here.
            {
                MessageBox.Show("Error trying to set camera work mode.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Hides (makes invisible) the control panel which will be displayed once the camera engine starts
        /// </summary>
        ///
        /* JTZ: I add this method for user's debug purpose...use might show the control panel...so all the
         * settings (e.g. exposure time...etc.) are visible on this panel...user might hide it in his  formal
         * application.
         */
        public void ShowFactoryControlPanel( uint Left, uint Top)
        {
            String passWord = "123456";

            if (BufShowFactoryControlPanel(_deviceID, passWord) < 0)
            {
                MessageBox.Show("Error trying to show camera control panel.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Hides (makes invisible) the control panel which will be displayed once the camera engine starts
        /// </summary>
        public void HideFactoryControlPanel()
        {
            if ( BufHideFrameControlPanel() < 0)
            {
                MessageBox.Show("Error trying to hide camera control panel.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Starts frame grabbing after camera resources prepared. After call, user should see images in video window
        /// </summary>
        /// <param name="totalFrames"></param>
        public void StartFrameGrab(int totalFrames)
        {
            // Install frame call back.
            //BufInstallFrameHooker( 0, frameDelegate); // I get raw data in this example.
            BufInstallFrameHooker(1, frameDelegate); // BMP data
            if ( BufStartFrameGrab( totalFrames) < 0)
            {
                MessageBox.Show("Error trying to start frame grabbing images.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Stops frame grabbing, call if totalFrames set to INFINITE_FRAMES
        /// </summary>
        public void StopFrameGrab()
        {
            // Install frame call back.
            BufInstallFrameHooker( 0, null ); // Unhooker the callback.
            if (BufStopFrameGrab() < 0)
            {
                MessageBox.Show("Error trying to stop frame grabbing images.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        //Note: only three elements _resolution, _binMode and _imageRendorFitWindow are used by this function, all others are ignored.
        /// <summary>
        /// Set the resolution (including capture and render)
        /// </summary>
        /// <param name="resolution"></param>
        /// <param name="binMode"></param>
        public void SetResolution( RESOLUTION resolution, int binMode )
        {
            this.SetMaxXY(resolution);
            _imgControl._binMode = binMode;

            if (BufSetCustomizedResolution(_deviceID, _imgControl._rowSize, _imgControl._columnSize, _imgControl._binMode, 4) < 0)
            {
                MessageBox.Show("Error trying to set camera resolution, bin mode, and image rendor fitting.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void SetMaxXY(RESOLUTION res)
        {
            //Set maximum X and Y start positions based on resolution
            switch (res)
            {
                case RESOLUTION.TINY:
                    _maxX = 1392;
                    _maxY = 256;
                    break;
                case RESOLUTION.LITTLE:
                    _maxX = 1392;
                    _maxY = 344;
                    break;
                case RESOLUTION.SMALL:
                    _maxX = 1392;
                    _maxY = 520;
                    break;
                case RESOLUTION.NORMAL:
                    _maxX = 1392;
                    _maxY = 1040;
                    break;
                default:
                    MessageBox.Show("Resolution not defined, unable to set maximum X and Y start positions.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
                    break;
            }
            _imgControl._rowSize = _maxX;
            _imgControl._columnSize = _maxY;
        }

        //Note: only two elements _xStart and _yStart are used by this function, all others are ignored.
        /// <summary>
        /// Set the start position of ROI
        /// </summary>
        /// <param name="Xstart"></param>
        /// <param name="Ystart"></param>
        public void SetStartPosition(int Xstart, int Ystart)
        {
            _imgControl._xStart = Xstart;
            _imgControl._yStart = Ystart;

            if (BufSetStartPosition(_deviceID, Xstart, Ystart) < 0)
            {
                MessageBox.Show("Error trying to set camera X and Y start positions.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        //Note: only three elements _greenGain, _blueGain and _redGain are used by this function, all others are ignored.
        /// <summary>
        /// Set RGB Gain parameters
        /// </summary>
        /// <param name="redGain"></param>
        /// <param name="greenGain"></param>
        /// <param name="blueGain"></param>
        public void SetGain(int redGain, int greenGain, int blueGain)
        {
            _imgControl._redGain = redGain;
            _imgControl._greenGain = greenGain;
            _imgControl._blueGain = blueGain;

            if (BufSetGains(_deviceID, redGain, greenGain, blueGain) < 0)
            {
                MessageBox.Show("Error trying to set camera RGB gains.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        //Note: only two elements _maxExposureTimeIndex and _exposureTime are used by this function, all others are ignored.
        /// <summary>
        /// Set camera exposure parameters
        /// </summary>
        /// <param name="expTime"></param>
        public void SetExposureTime( int expTime)
        {
            _imgControl._exposureTime = expTime*1000; //convert milli to microseconds

            if (BufSetExposureTime(_deviceID, (_imgControl._exposureTime / 50)) < 0)
            {
                MessageBox.Show("Error trying to set camera exposure settings.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        //Set the Gamma, Contrast and Brightness parameters
        //Note: only four elements _gamma, _contrast, _bright and _sharpLevel are used by this function, all others are ignored.
        public void SetGammaValue(int gamma, int contrast, int brightness, SHARPNESS_LEV sharpLev)
        {
            _imgControl._gamma = gamma;
            _imgControl._contrast = contrast;
            _imgControl._bright = brightness;
            _imgControl._sharpLevel = (int) sharpLev;

            if ( BufSetGamma( gamma, contrast, brightness, (int)sharpLev) < 0)
            {
                MessageBox.Show("Error trying to set camera gamma, contrast, brightness, and sharpness levels.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        
        //Note: only three elements _blkWhtmode, _horzMirror and _vertFlip are used by this function, all others are ignored.
        /// <summary>
        /// Set the BWMode, HorizontalMirror and VerticalFlip parameters
        /// </summary>
        /// <param name="bwMode"></param>
        /// <param name="horzMirror"></param>
        /// <param name="vertFlip"></param>
        public void SetShowMode(bool bwMode, bool horzMirror, bool vertFlip)
        {
            _imgControl._blkWhtMode = ( bwMode ? 1 : 0 );
            _imgControl._horzMirror = (horzMirror ? 1 : 0);
            _imgControl._vertFlip = (vertFlip ? 1 : 0);

            if ( BufSetBWMode( _imgControl._blkWhtMode, _imgControl._horzMirror, _imgControl._vertFlip) < 0 )
            {
                MessageBox.Show("Error trying to set camera B&W moode, horizontal mirror, and vertical flip settings.", _camError, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        
        public void AllocImageMem()
        {
            _pImage = Marshal.AllocHGlobal(pixelDepthBits * _maxX * _maxY);
        }

        public void FreeImageMem()
        {
            if (_pImage != IntPtr.Zero)
            {
                Marshal.FreeHGlobal(_pImage);
            }
        }
        
        #region Mightex interop functions for accessing BUF_USBCCDCamera_SDK_Stdcall.dll and BufferCameraUsblib.dll files
  
        //Call this function first, this function communicates with device driver to reserve resources
        //When the system uses NTFS use WINNT, for FAT32 use WINDOWS
        /*
         * JTZ: Note that I assume we put BUF_USBCCDCamera_SDK_Stdcall.dll and MtUsblib.dll in windows\system32.
         */

        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_InitDevice", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufInitDevice();


        //Call this function before the app terminates, it releases all resources
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_UnInitDevice", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufUnInitDevice();

        //The module number and serial number are what appear if one calls the
        //SDK_HANDLE_API BUFCCDUSB_ShowOpenDeviceDialog() method.
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_GetModuleNoSerialNo", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufGetModuleNoSerialNo(int deviceID, StringBuilder moduleNo, StringBuilder serialNo);

        //Add device to working set, deviceID is a one base index, so if InitDevice returns 2 for example, there devices at 1 and 2.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_AddDeviceToWorkingSet", CallingConvention = CallingConvention.StdCall)]
        private static extern uint BufAddDeviceToWorkingSet(int deviceID);

        //Remove device from working set. 
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_RemoveDeviceFromWorkingSet", CallingConvention = CallingConvention.StdCall)]
        private static extern uint BufRemoveDeviceFromWorkingSet(int deviceID);

        //Camera has multithread engine internally, which is responsible for all the frame grabbing, raw data to RGB data conversion etc. functions. 
        //User MUST start this engine for all the following camera related operations
        //ParentHandle ?The window handle of the main form of user’s application, as the engine relies on
        //Windows Message Queue, it needs a parent window handle
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_StartCameraEngine", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufStartCameraEngine(IntPtr parentHandle, uint cameraBitOption);

        //Stops the started camera engine.
        //returns:  -1 If the function fails (e.g. invalid device handle or if the engine is NOT started), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_StopCameraEngine", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufStopCameraEngine();

        //Sets camera to either "video" mode - continuously deliver frames to PC or
        //"external trigger" mode - camera waits for external trigger to capture 1 frame
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetCameraWorkMode", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetCameraWorkMode( int deviceID, int WorkMode);

        //Showes (makes visible) the factory control panel which will be displayed once the camera engine starts
        //returns:  -1 If the function fails (e.g. invalid device handle or if the engine is NOT started yet), 1 if the call succeeds.
        /*
         * JTZ: I add this API for user debug purpose. 
         */
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_ShowFactoryControlPanel", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufShowFactoryControlPanel( int deviceID, String password );

        //Hides (makes invisible) the control panel which will be displayed once the camera engine starts
        //returns:  -1 If the function fails (e.g. invalid device handle or if the engine is NOT started yet), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_HideFactoryControlPanel", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufHideFrameControlPanel();

            //Starts frame grabbing after camera resources prepared.
        //After call, user should see images in video window
        //returns:  -1 If the function fails (e.g. invalid device handle or if the engine is NOT started yet), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_StartFrameGrab", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufStartFrameGrab(int totalFrames);

        //Stops frame grabbing, call if totalFrames set to INFINITE_FRAMES
        //returns:  -1 If the function fails (e.g. invalid device handle or if the engine is NOT started yet), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_StopFrameGrab", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufStopFrameGrab();

        //Set the resolution (including capture and render)
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only three elements _resolution, _binMode and _imageRendorFitWindow are used by this function, all others are ignored.
        
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only three elements _resolution, _binMode and _imageRendorFitWindow are used by this function, all others are ignored.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetCustomizedResolution", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetCustomizedResolution(int deviceID, int rowSize, int columnSize, int bin, int bufferCnt);


        //Set the start position of ROI
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only two elements _xStart and _yStart are used by this function, all others are ignored.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetXYStart", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetStartPosition( int deviceID, int xStart, int yStart);

        //Set RGB Gains parameters
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only three elements _greenGain, _blueGain and _redGain are used by this function, all others are ignored.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetGains", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetGains( int deviceID, int redGain, int greenGain, int blueGain);

        //Set exposure parameters
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only two elements _maxExposureTimeIndex and _exposureTime are used by this function, all others are ignored.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetExposureTime", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetExposureTime( int deviceID, int exposureTime);

        //Set the Gamma, Contrast and Brightness parameters
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        //Note: only four elements _gamma? _contrast? _bright and _sharpLevel are used by this function, all others are ignored.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetGamma", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetGamma( int gamma, int contrast, int brightness, int sharpLevel);

        //Automatically set white balance, set proper exposure time and put white paper in front of camera
        //returns:  -1 If the function fails (e.g. invalid device handle), 1 if the call succeeds.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetBWMode", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetBWMode( int bWMode, int hMirror, int vFlip);

        // JTZ: we allow user to install a callback for each grabbed frame.
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_InstallFrameHooker", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufInstallFrameHooker( int FrameType, Delegate FrameCallBack);

        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_InstallUSBDeviceHooker", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufInstallUSBDeviceHooker( Delegate USBDeviceCallBack);
        
        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetGPIOConfig", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetGPIOConfig( int deviceID, byte configByte);

        [DllImport("BUF_USBCCDCamera_SDK_Stdcall.dll", EntryPoint = "BUFCCDUSB_SetGPIOInOut", CallingConvention = CallingConvention.StdCall)]
        private static extern int BufSetGPIOInOut( int deviceID, byte outputByte, out byte InByte );

        #endregion
    }

}
