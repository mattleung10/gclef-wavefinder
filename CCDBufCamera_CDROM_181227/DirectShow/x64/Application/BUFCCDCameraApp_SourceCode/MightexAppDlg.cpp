// MightexAppDlg.cpp : implementation file
//
#include "stdafx.h"
#include "MightexApp.h"
#include "MightexAppDlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CMightexAppDlg dialog
extern CMightexAppApp theApp;

CMightexAppDlg::CMightexAppDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CMightexAppDlg::IDD, pParent)
{
	//{{AFX_DATA_INIT(CMightexAppDlg)
	m_FileName_Edit = _T("");
	m_SnapshotNum_Edit = _T("");
	m_Width_Edit = _T("");
	m_Height_Edit = _T("");
	m_Exposure_COMBO = -1;
	m_JPEGFile_CHK = FALSE;
	m_Append_DateTime_CHK = FALSE;
	m_FilePath_Edit = _T("");
	m_Compressor_CHK = FALSE;
	m_Compressor_COMBO = -1;
	m_FrameRate_Edit = _T("");
	//}}AFX_DATA_INIT
	// Note that LoadIcon does not require a subsequent DestroyIcon in Win32
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CMightexAppDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CMightexAppDlg)
	DDX_Control(pDX, IDC_Compressor_CHK, m_Compressor_CHK_Ctrl);
	DDX_Control(pDX, IDC_SetFrameRateBtn, m_SetFrameRateBtn);
	DDX_Control(pDX, IDC_Exposure_COMBO, m_Exposure_COMBO_Ctrl);
	DDX_Control(pDX, IDC_Blue_SLIDER, m_Blue_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_Red_SLIDER, m_Red_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_SetResolutionBtn, m_SetResolutionBtn);
	DDX_Control(pDX, IDC_Compressor_COMBO, m_Compressor_COMBO_Ctrl);
	DDX_Control(pDX, IDC_YStart_SLIDER, m_YStart_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_XStart_SLIDER, m_XStart_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_Device_COMBO, m_Device_COMBO_Ctrl);
	DDX_Control(pDX, IDC_Green_SLIDER, m_Green_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_Exposure_SLIDER, m_Exposure_SLIDER_Ctrl);
	DDX_Control(pDX, IDC_ConnectBtn2, m_ConnectBtn2);
	DDX_Control(pDX, IDC_ConnectBtn, m_ConnectBtn);
	DDX_Text(pDX, IDC_FileName_Edit, m_FileName_Edit);
	DDX_Text(pDX, IDC_SnapshotNum_Edit, m_SnapshotNum_Edit);
	DDX_Text(pDX, IDC_Width_Edit, m_Width_Edit);
	DDX_Text(pDX, IDC_Height_Edit, m_Height_Edit);
	DDX_CBIndex(pDX, IDC_Exposure_COMBO, m_Exposure_COMBO);
	DDX_Check(pDX, IDC_JPEGFile_CHK, m_JPEGFile_CHK);
	DDX_Check(pDX, IDC_Append_DateTime_CHK, m_Append_DateTime_CHK);
	DDX_Text(pDX, IDC_FilePath_Edit, m_FilePath_Edit);
	DDX_Check(pDX, IDC_Compressor_CHK, m_Compressor_CHK);
	DDX_CBIndex(pDX, IDC_Compressor_COMBO, m_Compressor_COMBO);
	DDX_Text(pDX, IDC_FrameRate_Edit, m_FrameRate_Edit);
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CMightexAppDlg, CDialog)
	//{{AFX_MSG_MAP(CMightexAppDlg)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_ConnectBtn, OnConnectBtn)
	ON_BN_CLICKED(IDC_SnapshotBtn, OnSnapshotBtn)
	ON_BN_CLICKED(IDC_ConnectBtn2, OnConnectBtn2)
	ON_BN_CLICKED(IDC_SetResolutionBtn, OnSetResolutionBtn)
	ON_WM_HSCROLL()
	ON_CBN_SELCHANGE(IDC_Exposure_COMBO, OnSelchangeExposureCOMBO)
	ON_WM_VSCROLL()
	ON_BN_CLICKED(IDC_Compressor_CHK, OnCompressorCHK)
	ON_BN_CLICKED(IDC_SetFrameRateBtn, OnSetFrameRateBtn)
	ON_BN_CLICKED(IDC_WorkMode_RADIO1, OnWorkModeRADIO)
	ON_BN_CLICKED(IDC_WorkMode_RADIO2, OnWorkModeRADIO2)
	ON_BN_CLICKED(IDC_PropertyPageBtn, OnPropertyPageBtn)
	ON_BN_CLICKED(IDC_SelectFilePathBtn, OnSelectFilePathBtn)
	ON_WM_TIMER()
	ON_WM_CLOSE()
	ON_CBN_SELCHANGE(IDC_Device_COMBO, OnSelchangeDeviceCOMBO)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CMightexAppDlg message handlers

BOOL CMightexAppDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon
	
	Init();//INIT Variables and Controls

	return TRUE;  // return TRUE  unless you set the focus to a control
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model, 
//  this is automatically done for you by the framework.

void CMightexAppDlg::OnPaint() 
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, (WPARAM) dc.GetSafeHdc(), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CMightexAppDlg::OnQueryDragIcon()
{
	return (HCURSOR) m_hIcon;
}


/////////////////////////////////////////////////////////////////////////////

void CMightexAppDlg::Init()
{//INIT Variables and Controls
	//////////////////////////////////////////////////////////////////////////
	//INIT Variables

	HRESULT hr;
	inited = 0;
	
	mightex_VideoShow = new CMightex_VideoShow;
	hr = mightex_VideoShow->Init();
    if (FAILED(hr))
    {
		EndDialog(IDCANCEL);
		MessageBox("No Camera!", "Alert!", MB_OK);
        return;
    }
	ghApp = NULL;

	m_FileName_Edit = "cap";
	m_SnapshotNum_Edit = "1";
	m_Exposure_COMBO = 2;
	m_FrameRate_Edit = "30.00";
	
	UpdateData(FALSE);
	//////////////////////////////////////////////////////////////////////////

	//////////////////////////////////////////////////////////////////////////
	//INIT Controls

	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;
	mightex_VideoShow->GetCameraControl(cameraCtrl, cameraGlobalCtl);

	//init Device_COMBO and DeviceName_STATIC
	for(int n = 0; n < cameraGlobalCtl.cameraCount; n++)
		m_Device_COMBO_Ctrl.AddString(CString(cameraGlobalCtl.camNames[n]));
	m_Device_COMBO_Ctrl.SetCurSel(0);
	SetDlgItemText(IDC_DeviceName_STATIC, "Device: "+CString(cameraGlobalCtl.camNames[0]));
	
	//init WorkMode_RADIO
	CheckRadioButton(IDC_WorkMode_RADIO1, IDC_WorkMode_RADIO2, IDC_WorkMode_RADIO1);
	
	//init Resolution_Edit
	CheckRadioButton(IDC_Resolution_RADIO2, IDC_Resolution_RADIO6, IDC_Resolution_RADIO2);
	SetDlgItemInt(IDC_Width_Edit, cameraCtrl.width, FALSE);
	SetDlgItemInt(IDC_Height_Edit, cameraCtrl.height, FALSE);

	char str[32];
	sprintf(str, "%d x %d\0", s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].width, s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].height);
	SetDlgItemText(IDC_Resolution_RADIO3, str);
	
	char str1[32], str2[32], str3[32];
	switch(cameraCtrl.DeviceType) {
	case ICX424M:
	case ICX424C:
		sprintf(str1, "%d x %d(1:2)Bin\0", frameSize_ICX424[1].width, frameSize_ICX424[1].height);
		sprintf(str2, "%d x %d(1:3)Bin\0", frameSize_ICX424[2].width, frameSize_ICX424[2].height);
		sprintf(str3, "%d x %d(1:4)Bin\0", frameSize_ICX424[3].width, frameSize_ICX424[3].height);
		break;
	case ICX445AL:
	case ICX445AQ:
		sprintf(str1, "%d x %d(1:2)Bin\0", frameSize_ICX445[1].width, frameSize_ICX445[1].height);
		sprintf(str2, "%d x %d(1:3)Bin\0", frameSize_ICX445[2].width, frameSize_ICX445[2].height);
		sprintf(str3, "%d x %d(1:4)Bin\0", frameSize_ICX445[3].width, frameSize_ICX445[3].height);
		break;
	case ICX205AL:
	case ICX205AK:
	case ICX285AL:
	case ICX285AQ:
		sprintf(str1, "%d x %d(1:2)Bin\0", frameSize_ICX205[1].width, frameSize_ICX205[1].height);
		sprintf(str2, "%d x %d(1:3)Bin\0", frameSize_ICX205[2].width, frameSize_ICX205[2].height);
		sprintf(str3, "%d x %d(1:4)Bin\0", frameSize_ICX205[3].width, frameSize_ICX205[3].height);
		break;
	case ICX274AL:
	case ICX274AQ:
		sprintf(str1, "%d x %d(1:2)Bin\0", frameSize_ICX274[1].width, frameSize_ICX274[1].height);
		sprintf(str2, "%d x %d(1:3)Bin\0", frameSize_ICX274[2].width, frameSize_ICX274[2].height);
		sprintf(str3, "%d x %d(1:4)Bin\0", frameSize_ICX274[3].width, frameSize_ICX274[3].height);
		break;
	default:
		break;
	}
	SetDlgItemText(IDC_Resolution_RADIO4, str1);
	SetDlgItemText(IDC_Resolution_RADIO5, str2);
	SetDlgItemText(IDC_Resolution_RADIO6, str3);
	if ((cameraCtrl.DeviceType == ICX424C)||(cameraCtrl.DeviceType == ICX205AK)||(cameraCtrl.DeviceType == ICX285AQ)||(cameraCtrl.DeviceType == ICX274AQ)) 
	{
		GetDlgItem(IDC_Resolution_RADIO4)->EnableWindow(FALSE);
		GetDlgItem(IDC_Resolution_RADIO5)->EnableWindow(FALSE);
		GetDlgItem(IDC_Resolution_RADIO6)->EnableWindow(FALSE);
	}
		
	//init Exposure_SLIDER
	char tempstr[32];
	m_Exposure_SLIDER_Ctrl.SetRange(1, 100);
	m_Exposure_SLIDER_Ctrl.SetPos(cameraCtrl.exposureTime / 20); //20 = 1000 / 50
	sprintf(tempstr, "Exposure Time: ( %dms )", cameraCtrl.exposureTime / 20); //20 = 1000 / 50
	SetDlgItemText(IDC_ExposureTime_STATIC, CString( tempstr ) );
	
	//init Green\Red\Blue_SLIDER
	m_Green_SLIDER_Ctrl.SetRange(6, 41);
	m_Green_SLIDER_Ctrl.SetPos(cameraCtrl.greenGain);
	m_Red_SLIDER_Ctrl.SetRange(6, 41);
	m_Red_SLIDER_Ctrl.SetPos(cameraCtrl.redGain);
	m_Blue_SLIDER_Ctrl.SetRange(6, 41);
	m_Blue_SLIDER_Ctrl.SetPos(cameraCtrl.blueGain);
	if ((cameraCtrl.DeviceType == ICX205AK)||(cameraCtrl.DeviceType == ICX285AQ)||(cameraCtrl.DeviceType == ICX274AQ)) 
	{
		m_Red_SLIDER_Ctrl.ShowWindow(TRUE);
		m_Blue_SLIDER_Ctrl.ShowWindow(TRUE);
	}
	else
	{
		SetDlgItemText(IDC_Red_STATIC, CString("") );
		SetDlgItemText(IDC_Green_STATIC, CString("Global") );
		SetDlgItemText(IDC_Blue_STATIC, CString("") );		
	}
	
	//init Compressor_COMBO
	CStringList m_CompressorList;
	hr = mightex_VideoShow->AddCompressorsToList(m_CompressorList);
	if(FAILED(hr))
		m_Compressor_CHK_Ctrl.EnableWindow(FALSE);
	else
	{
		for(POSITION pos = m_CompressorList.GetHeadPosition(); pos != NULL;)
		{
			m_Compressor_COMBO_Ctrl.AddString(m_CompressorList.GetNext(pos));
		}
		m_CompressorList.RemoveAll();
		m_Compressor_COMBO_Ctrl.SetCurSel(0);
	}
	
	OnSetResolutionBtn();

	SetTimer(1, 100, NULL);

	inited =1;
	//////////////////////////////////////////////////////////////////////////	
}

CMightexAppDlg::~CMightexAppDlg()
{
	if(mightex_VideoShow) delete mightex_VideoShow;
	mightex_VideoShow = NULL;
	CoUninitialize();
}

void CMightexAppDlg::OnConnectBtn() 
{//Capturing
	if(!(mightex_VideoShow->GetCaptureState()))
	{
		SetDlgItemText(IDC_ConnectBtn, "StopCapture");
		m_SetResolutionBtn.EnableWindow(FALSE);
		m_SetFrameRateBtn.EnableWindow(FALSE);
		m_Exposure_SLIDER_Ctrl.EnableWindow(FALSE);
		m_Exposure_COMBO_Ctrl.EnableWindow(FALSE);
		m_Device_COMBO_Ctrl.EnableWindow(FALSE);

		UpdateData();
		WCHAR TargetFile[256];
		// Convert target filename
		MultiByteToWideChar(CP_ACP, 0, (const char *)(m_FilePath_Edit+m_FileName_Edit+".avi"), -1, 
			TargetFile, NUMELMS(TargetFile));
		int compressorNum = -1;
		if (m_Compressor_CHK)
			compressorNum = m_Compressor_COMBO;
		mightex_VideoShow->Capture(TargetFile, compressorNum);

		SetDlgItemText(IDC_State_STATIC, "Capturing...");	
	}
	else
	{		
		mightex_VideoShow->StopCapture();
		
		SetDlgItemText(IDC_ConnectBtn, "Capture");
		SetDlgItemText(IDC_State_STATIC, "");	
		m_SetResolutionBtn.EnableWindow(TRUE);
		m_SetFrameRateBtn.EnableWindow(TRUE);
		m_Exposure_SLIDER_Ctrl.EnableWindow(TRUE);
		m_Exposure_COMBO_Ctrl.EnableWindow(TRUE);
		m_Device_COMBO_Ctrl.EnableWindow(TRUE);
	}
}

void CMightexAppDlg::OnConnectBtn2() 
{//Previewing
	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;
	mightex_VideoShow->GetCameraControl(cameraCtrl, cameraGlobalCtl);

	if(!(mightex_VideoShow->GetPreviewState()))
	{
		if (!ghApp) {
			// Create the video window.  The WS_CLIPCHILDREN style is required.
			ghApp = CreateWindow(TEXT("Demo\0"), TEXT("MightexApp Demo\0"), 
				WS_OVERLAPPEDWINDOW | WS_CAPTION | WS_CLIPCHILDREN, 
				CW_USEDEFAULT, CW_USEDEFAULT, 
				cameraCtrl.width, cameraCtrl.height, 
				m_hWnd, 0, theApp.m_hInstance, 0);
		}
		mightex_VideoShow->Preview(ghApp);
		SetDlgItemText(IDC_ConnectBtn2, "StopPreview");
		m_Device_COMBO_Ctrl.EnableWindow(FALSE);
	}
	else
	{
		mightex_VideoShow->StopPreview();
		SetDlgItemText(IDC_ConnectBtn2, "Preview");
		m_Device_COMBO_Ctrl.EnableWindow(TRUE);
	}
}

void CMightexAppDlg::OnSnapshotBtn() 
{//Snapshot
	UpdateData();
	int snapshotNum = atoi((const char *)m_SnapshotNum_Edit);
	mightex_VideoShow->Snapshot((char *)(const char *)(m_FilePath_Edit+m_FileName_Edit), 
		TRUE, m_JPEGFile_CHK, m_Append_DateTime_CHK, FALSE, snapshotNum, 0);

	char stateMsg[16];
	sprintf(stateMsg, "Snapshot %dp", snapshotNum);
	SetDlgItemText(IDC_Snapshot_STATIC,stateMsg);
}

void CMightexAppDlg::OnSetResolutionBtn() 
{//SetResolution
	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;
	mightex_VideoShow->GetCameraControl(cameraCtrl, cameraGlobalCtl);
	int MAX_width = s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].width;
	int MAX_height = s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].height;
	
	UpdateData();
	int width = MAX_width, height = MAX_height;
	int bin = 0;

	if(IsDlgButtonChecked(IDC_Resolution_RADIO2))
	{
		width = atoi((const char *)m_Width_Edit);
		height = atoi((const char *)m_Height_Edit);
	}
	else if(IsDlgButtonChecked(IDC_Resolution_RADIO4))
		bin = 1;
	else if(IsDlgButtonChecked(IDC_Resolution_RADIO5))
		bin = 2;
	else if(IsDlgButtonChecked(IDC_Resolution_RADIO6))
		bin = 3;
		
	mightex_VideoShow->SetResolution(width, height, bin);
	
	char stateMsg[16];
	sprintf(stateMsg, "%dx%d", width, height);
	SetDlgItemText(IDC_Resolution_STATIC, stateMsg);

	if(MAX_width-width>0)
	{
		m_XStart_SLIDER_Ctrl.SetRange(0, MAX_width-width);
		m_XStart_SLIDER_Ctrl.EnableWindow(TRUE);
	}
	else
	{
		m_XStart_SLIDER_Ctrl.ClearTics();
		m_XStart_SLIDER_Ctrl.EnableWindow(FALSE);
	}
	m_XStart_SLIDER_Ctrl.SetPos(0);
	
	if(MAX_height-height>0)
	{
		m_YStart_SLIDER_Ctrl.SetRange(0, MAX_height-height);		
		m_YStart_SLIDER_Ctrl.EnableWindow(TRUE);
	}
	else
	{
		m_YStart_SLIDER_Ctrl.ClearTics();
		m_YStart_SLIDER_Ctrl.EnableWindow(FALSE);
	}
	m_YStart_SLIDER_Ctrl.SetPos(0);
}

void CMightexAppDlg::OnSelchangeExposureCOMBO() 
{//Changing Exposure Time Range
	UpdateData();
	int frameTimePos = m_Exposure_SLIDER_Ctrl.GetPos();
	float f_frameTime = frameTimePos * MAX_EXPOSURETIME[m_Exposure_COMBO] / 100.000;
	int i_frameTime = frameTimePos * MAX_EXPOSURETIME[m_Exposure_COMBO] * 10 / 50;//50 Microsecond UNIT
	mightex_VideoShow->SetExposureTime(i_frameTime);
	
	char frameTimeStr[32];
	sprintf(frameTimeStr, "Exposure Time: ( %gms )", f_frameTime);
	SetDlgItemText(IDC_ExposureTime_STATIC, CString( frameTimeStr ) );
}

void CMightexAppDlg::OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar) 
{//Changing Exposure Time
	if(&m_Exposure_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar))
	{
		int frameTimePos = m_Exposure_SLIDER_Ctrl.GetPos();
		float f_frameTime = frameTimePos * MAX_EXPOSURETIME[m_Exposure_COMBO] / 100.000;
		//int i_frameTime = (int(f_frameTime) == 0 ? 1 : int(f_frameTime));
		int i_frameTime = frameTimePos * MAX_EXPOSURETIME[m_Exposure_COMBO] * 10 / 50;//50 Microsecond UNIT
		mightex_VideoShow->SetExposureTime(i_frameTime);

		char frameTimeStr[32];
		sprintf(frameTimeStr, "Exposure Time: ( %gms )", f_frameTime);
		SetDlgItemText(IDC_ExposureTime_STATIC, CString( frameTimeStr ) );
	}
	
	CDialog::OnHScroll(nSBCode, nPos, pScrollBar);
}

void CMightexAppDlg::OnVScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar) 
{//Changing Red\Green\Blue Color or XYStart
	if(&m_Red_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar) ||
		&m_Green_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar) ||
		&m_Blue_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar))
	{
		int redGain = m_Red_SLIDER_Ctrl.GetPos();
		int greenGain = m_Green_SLIDER_Ctrl.GetPos();
		int blueGain = m_Blue_SLIDER_Ctrl.GetPos();
		mightex_VideoShow->SetGains(redGain, greenGain, blueGain);
	}
	
	if(&m_XStart_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar))
	{
		int xStart = m_XStart_SLIDER_Ctrl.GetPos();
		int yStart = m_YStart_SLIDER_Ctrl.GetPos();
		mightex_VideoShow->SetXYStart(xStart, yStart);
	}

	if(&m_YStart_SLIDER_Ctrl == ((CSliderCtrl *)pScrollBar))
	{
		int xStart = m_XStart_SLIDER_Ctrl.GetPos();
		int yStart = m_YStart_SLIDER_Ctrl.GetPos();
		mightex_VideoShow->SetXYStart(xStart, yStart);
	}
	
	CDialog::OnVScroll(nSBCode, nPos, pScrollBar);
}

void CMightexAppDlg::OnCompressorCHK() 
{//Enalbing or Disalbing Compressor_COMBO
	m_Compressor_CHK = !m_Compressor_CHK;
	m_Compressor_COMBO_Ctrl.EnableWindow(m_Compressor_CHK);
}

void CMightexAppDlg::OnSetFrameRateBtn() 
{//SetFrameRate
	UpdateData();
	double frameRate = atof((const char *)m_FrameRate_Edit);
	mightex_VideoShow->SetStreamFrameRate(10000000 / frameRate);
	
}

void CMightexAppDlg::OnWorkModeRADIO() 
{//SetCameraWorkMode
	if(IsDlgButtonChecked(IDC_WorkMode_RADIO1))
		mightex_VideoShow->SetCameraWorkMode(0);
}

void CMightexAppDlg::OnWorkModeRADIO2()
{//SetCameraWorkMode
	if(IsDlgButtonChecked(IDC_WorkMode_RADIO2))
		mightex_VideoShow->SetCameraWorkMode(1);	
}

void CMightexAppDlg::OnPropertyPageBtn() 
{//OpenPropertyPages
	mightex_VideoShow->OpenPropertyPages(m_hWnd);
}

LRESULT CMightexAppDlg::WindowProc(UINT message, WPARAM wParam, LPARAM lParam) 
{//WindowProc
	if(message == WM_ACTIVATE) 
		if(LOWORD(wParam) == WA_ACTIVE)
			OnDlgActive();

	return CDialog::WindowProc(message, wParam, lParam);
}

void CMightexAppDlg::OnDlgActive()
{//OnDlgActive
	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;

	if(inited == 0)
		return;

	mightex_VideoShow->GetCameraControl(cameraCtrl, cameraGlobalCtl);

	if(cameraCtrl.workMode)
		CheckRadioButton(IDC_WorkMode_RADIO1, IDC_WorkMode_RADIO2, IDC_WorkMode_RADIO2);
	else
		CheckRadioButton(IDC_WorkMode_RADIO1, IDC_WorkMode_RADIO2, IDC_WorkMode_RADIO1);

	if(cameraCtrl.bin == 0)
		CheckRadioButton(IDC_Resolution_RADIO2, IDC_Resolution_RADIO6, IDC_Resolution_RADIO2);
	else if(cameraCtrl.bin == 1)
		CheckRadioButton(IDC_Resolution_RADIO2, IDC_Resolution_RADIO6, IDC_Resolution_RADIO4);
	else if(cameraCtrl.bin == 2)
		CheckRadioButton(IDC_Resolution_RADIO2, IDC_Resolution_RADIO6, IDC_Resolution_RADIO5);
	else
		CheckRadioButton(IDC_Resolution_RADIO2, IDC_Resolution_RADIO6, IDC_Resolution_RADIO6);
	
	SetDlgItemInt(IDC_Width_Edit, cameraCtrl.width, FALSE);
	SetDlgItemInt(IDC_Height_Edit, cameraCtrl.height, FALSE);
	
	int i = m_Exposure_COMBO_Ctrl.GetCurSel();
	if(cameraCtrl.exposureTime >= MAX_EXPOSURETIME[i] * 20)
	{
		if(cameraCtrl.exposureTime >= MAX_EXPOSURETIME[2] * 20)
			i = 3;
		else if(cameraCtrl.exposureTime >= MAX_EXPOSURETIME[1] * 20)
			i = 2;
		else
			i = 1;
		m_Exposure_COMBO_Ctrl.SetCurSel(i);
	}
	m_Exposure_SLIDER_Ctrl.SetPos(100 * cameraCtrl.exposureTime * 50 / (MAX_EXPOSURETIME[i] * 1000)); //20 = 1000 / 50
	float f_frameTime = cameraCtrl.exposureTime * 50 / 1000.000;
	char tempstr[32];
	sprintf(tempstr, "Exposure Time: ( %gms )", f_frameTime); //20 = 1000 / 50
	SetDlgItemText(IDC_ExposureTime_STATIC, CString( tempstr ) );

	if((cameraCtrl.bin == 0) && (s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].width - cameraCtrl.width > 0))
	{
		m_XStart_SLIDER_Ctrl.SetRange(0, s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].width - cameraCtrl.width);
		m_XStart_SLIDER_Ctrl.SetPos(cameraCtrl.xStart);
		m_XStart_SLIDER_Ctrl.EnableWindow(TRUE);
	}
	else
	{
		m_XStart_SLIDER_Ctrl.ClearTics();
		m_XStart_SLIDER_Ctrl.SetPos(0);
		m_XStart_SLIDER_Ctrl.EnableWindow(FALSE);
	}
	
	if((cameraCtrl.bin == 0) && (s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].height - cameraCtrl.height > 0))
	{
		m_YStart_SLIDER_Ctrl.SetRange(0, s_vidFrameSize[cameraCtrl.MAX_RESOLUTION].height - cameraCtrl.height);		
		m_YStart_SLIDER_Ctrl.SetPos(cameraCtrl.yStart);
		m_YStart_SLIDER_Ctrl.EnableWindow(TRUE);
	}
	else
	{
		m_YStart_SLIDER_Ctrl.ClearTics();
		m_YStart_SLIDER_Ctrl.SetPos(0);
		m_YStart_SLIDER_Ctrl.EnableWindow(FALSE);
	}
	
	m_Green_SLIDER_Ctrl.SetPos(cameraCtrl.greenGain);
	m_Red_SLIDER_Ctrl.SetPos(cameraCtrl.redGain);
	m_Blue_SLIDER_Ctrl.SetPos(cameraCtrl.blueGain);
	
	float f_FrameRate = 10000000.00 / cameraCtrl.streamFrameRate;
	sprintf(tempstr, "%.2f\0", f_FrameRate);
	SetDlgItemText(IDC_FrameRate_Edit, tempstr);

	mightex_VideoShow->SetWindowCaption();
}

void CMightexAppDlg::OnSelectFilePathBtn() 
{//SelectFilePath
	char szPath[256];
	char szTitle[] = "File Path";
	char szDlgTitle[] = "select dir";
	BROWSEINFO bi;   
	LPITEMIDLIST lpi;   
    
	bi.hwndOwner = m_hWnd;   
	bi.pidlRoot = NULL;   
	bi.pszDisplayName = NULL;   
	bi.lpszTitle = szTitle;   
	bi.ulFlags = BIF_RETURNONLYFSDIRS|BIF_RETURNFSANCESTORS;   
	bi.lpfn = NULL;   
	bi.lParam = (LPARAM)szDlgTitle;   
	bi.iImage = 0;   
	lpi = SHBrowseForFolder(&bi);   
	if(lpi   ==   NULL) return;   
    
	LPMALLOC pMalloc;   
	SHGetMalloc(&pMalloc);   
	if(SHGetPathFromIDList(lpi,szPath))
		SetDlgItemText(IDC_FilePath_Edit, strcat(szPath, "\\"));
	pMalloc->Free(lpi);   
	pMalloc->Release();   
}

void CMightexAppDlg::OnTimer(UINT_PTR nIDEvent) 
{
	mightex_VideoShow->SetWindowCaption();	
	CDialog::OnTimer(nIDEvent);
}

void CMightexAppDlg::OnClose() 
{
	KillTimer(1);
	CDialog::OnClose();
}


/////////////////////////////////////////////////////////////////////////////


void CMightexAppDlg::OnSelchangeDeviceCOMBO() 
{
	int devID = m_Device_COMBO_Ctrl.GetCurSel() + 1;
	mightex_VideoShow->SetSelectCamera(devID);
	OnSelCamChange();
}

void CMightexAppDlg::OnSelCamChange()
{
	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;
	mightex_VideoShow->GetCameraControl(cameraCtrl, cameraGlobalCtl);

	SetDlgItemText(IDC_DeviceName_STATIC, "Device: "+CString(cameraGlobalCtl.camNames[m_Device_COMBO_Ctrl.GetCurSel()]));
	
	//init WorkMode_RADIO
	CheckRadioButton(IDC_WorkMode_RADIO1, IDC_WorkMode_RADIO2, IDC_WorkMode_RADIO1);
	
	//init Resolution_Edit
	SetDlgItemInt(IDC_Width_Edit, cameraCtrl.width, FALSE);
	SetDlgItemInt(IDC_Height_Edit, cameraCtrl.height, FALSE);
	CheckDlgButton(IDC_Decimation_CHK, cameraCtrl.bin);
	
	//init Exposure_SLIDER
	char tempstr[32];
	m_Exposure_SLIDER_Ctrl.SetRange(1, 100);
	m_Exposure_SLIDER_Ctrl.SetPos(cameraCtrl.exposureTime / 20); //20 = 1000 / 50
	sprintf(tempstr, "Exposure Time: ( %dms )", cameraCtrl.exposureTime / 20); //20 = 1000 / 50
	SetDlgItemText(IDC_ExposureTime_STATIC, CString( tempstr ) );
	
	//init Green\Red\Blue_SLIDER
	if ((cameraCtrl.DeviceType == ICX205AK)||(cameraCtrl.DeviceType == ICX285AQ)||(cameraCtrl.DeviceType == ICX274AQ)) 
	{
		m_Red_SLIDER_Ctrl.ShowWindow(TRUE);
		m_Blue_SLIDER_Ctrl.ShowWindow(TRUE);
	}
	else
	{
		SetDlgItemText(IDC_Red_STATIC, CString("") );
		SetDlgItemText(IDC_Green_STATIC, CString("Global") );
		SetDlgItemText(IDC_Blue_STATIC, CString("") );		
	}
		
	OnSetResolutionBtn();	
}