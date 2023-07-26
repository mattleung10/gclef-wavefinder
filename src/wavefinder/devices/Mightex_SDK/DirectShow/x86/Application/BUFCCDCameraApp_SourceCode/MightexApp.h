// MightexApp.h : main header file for the MIGHTEXAPP application
//

#if !defined(AFX_MIGHTEXAPP_H__D8F13704_6E1B_4365_94E9_39F2BCCF5631__INCLUDED_)
#define AFX_MIGHTEXAPP_H__D8F13704_6E1B_4365_94E9_39F2BCCF5631__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#ifndef __AFXWIN_H__
	#error include 'stdafx.h' before including this file for PCH
#endif

#include "resource.h"		// main symbols

/////////////////////////////////////////////////////////////////////////////
// CMightexAppApp:
// See MightexApp.cpp for the implementation of this class
//

class CMightexAppApp : public CWinApp
{
public:
	CMightexAppApp();

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CMightexAppApp)
	public:
	virtual BOOL InitInstance();
	//}}AFX_VIRTUAL

// Implementation

	//{{AFX_MSG(CMightexAppApp)
		// NOTE - the ClassWizard will add and remove member functions here.
		//    DO NOT EDIT what you see in these blocks of generated code !
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};


/////////////////////////////////////////////////////////////////////////////

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_MIGHTEXAPP_H__D8F13704_6E1B_4365_94E9_39F2BCCF5631__INCLUDED_)
