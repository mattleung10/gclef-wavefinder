// MightexAppDlg.h : header file
//

#if !defined(AFX_MIGHTEXAPPDLG_H__7F5C456E_B0BF_46E5_BECA_332074812E68__INCLUDED_)
#define AFX_MIGHTEXAPPDLG_H__7F5C456E_B0BF_46E5_BECA_332074812E68__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#include "VideoShow.h"//Add

/////////////////////////////////////////////////////////////////////////////
// CMightexAppDlg dialog

class CMightexAppDlg : public CDialog
{


// Construction
public:
	CMightexAppDlg(CWnd* pParent = NULL);	// standard constructor
	~CMightexAppDlg();//Add
	
	void Init();//Add
	void OnDlgActive();//Add
	void OnSelCamChange();//Add
	
	CMightex_VideoShow *mightex_VideoShow;//Add
	HWND ghApp;//Add
	int inited;//Add
	// Dialog Data
	//{{AFX_DATA(CMightexAppDlg)
	enum { IDD = IDD_MIGHTEXAPP_DIALOG };
	CButton	m_Compressor_CHK_Ctrl;
	CButton	m_SetFrameRateBtn;
	CComboBox	m_Exposure_COMBO_Ctrl;
	CSliderCtrl	m_Blue_SLIDER_Ctrl;
	CSliderCtrl	m_Red_SLIDER_Ctrl;
	CComboBox	m_Resolution_COMBO_Ctrl;
	CButton	m_SetResolutionBtn;
	CComboBox	m_Compressor_COMBO_Ctrl;
	CSliderCtrl	m_YStart_SLIDER_Ctrl;
	CSliderCtrl	m_XStart_SLIDER_Ctrl;
	CComboBox	m_Device_COMBO_Ctrl;
	CSliderCtrl	m_Green_SLIDER_Ctrl;
	CSliderCtrl	m_Exposure_SLIDER_Ctrl;
	CButton	m_ConnectBtn2;
	CButton	m_ConnectBtn;
	CString	m_FileName_Edit;
	CString	m_SnapshotNum_Edit;
	CString	m_Width_Edit;
	CString	m_Height_Edit;
	int		m_Resolution_COMBO;
	int		m_Resolution_RADIO;
	int		m_Exposure_COMBO;
	BOOL	m_JPEGFile_CHK;
	BOOL	m_Append_DateTime_CHK;
	CString	m_FilePath_Edit;
	BOOL	m_Compressor_CHK;
	int		m_Compressor_COMBO;
	CString	m_FrameRate_Edit;
	BOOL	m_Decimation_CHK;
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CMightexAppDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	virtual LRESULT WindowProc(UINT message, WPARAM wParam, LPARAM lParam);
	//}}AFX_VIRTUAL

// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	//{{AFX_MSG(CMightexAppDlg)
	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	afx_msg void OnConnectBtn();
	afx_msg void OnSnapshotBtn();
	afx_msg void OnConnectBtn2();
	afx_msg void OnSetResolutionBtn();
	afx_msg void OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar);
	afx_msg void OnSelchangeExposureCOMBO();
	afx_msg void OnVScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar);
	afx_msg void OnCompressorCHK();
	afx_msg void OnSetFrameRateBtn();
	afx_msg void OnWorkModeRADIO();
	afx_msg void OnWorkModeRADIO2();
	afx_msg void OnPropertyPageBtn();
	afx_msg void OnSelectFilePathBtn();
	afx_msg void OnTimer(UINT_PTR nIDEvent);
	afx_msg void OnClose();
	afx_msg void OnCancelMode();
	afx_msg void OnSelchangeDeviceCOMBO();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_MIGHTEXAPPDLG_H__7F5C456E_B0BF_46E5_BECA_332074812E68__INCLUDED_)
