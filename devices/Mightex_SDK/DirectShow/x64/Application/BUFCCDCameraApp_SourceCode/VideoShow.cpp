//------------------------------------------------------------------------------
// File: Mightex_BufferCCDSource.cpp
//
// Desc: DirectShow code - Video privewing and capturing.
//
// Copyright (c) Mightex Corporation.  All rights reserved.
//------------------------------------------------------------------------------

#include "stdafx.h"
#include "VideoShow.h"
#include <initguid.h>
#include "..\IMightex_BufferCCDSource.h"

CMightex_VideoShow::CMightex_VideoShow()
{
	g_pVW = NULL;
	g_pMC = NULL;
	g_pGraph = NULL;
	//g_pME = NULL;
	//g_pCapture = NULL;
	//g_pRC = NULL;
	//g_pMF = NULL;
    pMightex_BufferCCDSourceFilter = NULL;
	mIMightex_BufferCCDSource = NULL;
	pSC = NULL;
	pVideoRendererFilter = NULL;
	pSmartTee = NULL;
	pCompressor = NULL;
	pAviDest = NULL;
	pConfigInterleaving = NULL;
	//pConfigAviMux = NULL;
	pFileWriter = NULL;
	pFS = NULL;
	pSmartTeeOut0 = NULL;
	pSmartTeeOut1 = NULL;
	pSmartTeeIn = NULL;
	pVideoRendererFilterIn = NULL;
	pMightex_BufferCCDSourceFilterOut = NULL;
	old_ghApp = NULL;
	isPreviewing = FALSE;
	isCapturing = FALSE;
	isCompressing = FALSE;
}

CMightex_VideoShow::~CMightex_VideoShow()
{
	if(g_pMC) g_pMC->Stop();
	
	if(g_pGraph) g_pGraph->Release();
	//if(g_pME) g_pME->Release();
	//if(g_pCapture) g_pCapture->Release();
	//if(g_pRC) g_pVW->Release();
	//if(g_pMF) g_pMC->Release();
	if(g_pMC) g_pMC->Release();
	if(g_pVW) g_pVW->Release();

	if(pMightex_BufferCCDSourceFilter) pMightex_BufferCCDSourceFilter->Release();
	if(mIMightex_BufferCCDSource) mIMightex_BufferCCDSource->Release();//Can't the pointer be released?
	if(pSC) pSC->Release();

	if(pSmartTee) pSmartTee->Release();
	if(pVideoRendererFilter) pVideoRendererFilter->Release();
	if(pCompressor) pCompressor->Release();
	if(pAviDest) pAviDest->Release();
	if(pConfigInterleaving) pConfigInterleaving->Release();	
	//if(pConfigAviMux) pConfigAviMux->Release();	
	if(pFileWriter) pFileWriter->Release();
	if(pFS) pFS->Release();
	//if(pSmartTeeOut0) pSmartTeeOut0->Release();
	//if(pSmartTeeOut1) pSmartTeeOut1->Release();
	//if(pSmartTeeIn) pSmartTeeOut0->Release();
	//if(pVideoRendererFilterIn) pVideoRendererFilterIn->Release();
	//if(pMightex_BufferCCDSourceFilterOut) pMightex_BufferCCDSourceFilterOut->Release();

    // Release COM
    //CoUninitialize();
}

HRESULT CMightex_VideoShow::Init()
{	
	HRESULT hr;
    // Get DirectShow interfaces
    hr = GetInterfaces();
    if (FAILED(hr))
    {
        return hr;
    }

	hr = InitCameraControl();
    if (FAILED(hr))
    {
        return hr;
    }
		
	Snapshot("", FALSE, FALSE, FALSE, FALSE, 0, 0);//Init saveFileCtl
	

    // Add Mightex_BufferCCDSource filter to our graph.
    hr = g_pGraph->AddFilter(pMightex_BufferCCDSourceFilter, L"Mightex_BufferCCDSource Filter");
    if (FAILED(hr))
    {
        pMightex_BufferCCDSourceFilter->Release();
        return hr;
    }
    // Add Smart Tee filter to our graph.
    hr = g_pGraph->AddFilter(pSmartTee, L"Smart Tee Filter");
    if (FAILED(hr))
    {
        pSmartTee->Release();
        return hr;
    }
	
	//hr = ConnectFilters(g_pGraph, pMightex_BufferCCDSourceFilter, pSmartTee);
    if (FAILED(hr))
    {
        return hr;
    }

	// Add Video Renderer filter to our graph.
	hr = g_pGraph->AddFilter(pVideoRendererFilter, L"Video Renderer Filter");
	if (FAILED(hr))
	{
		pVideoRendererFilter->Release();
		return hr;
	}
	
	pSmartTeeOut0 = GetOutPin(pSmartTee, 0);
	pSmartTeeOut1 = GetOutPin(pSmartTee, 1);
	pSmartTeeIn = GetInPin(pSmartTee, 0);
	pVideoRendererFilterIn = GetInPin(pVideoRendererFilter, 0);
	pMightex_BufferCCDSourceFilterOut = GetOutPin(pMightex_BufferCCDSourceFilter, 0);
		
    return S_OK;
}

HRESULT CMightex_VideoShow::InitCameraControl()
{
	mIMightex_BufferCCDSource->GetCameraControl(cameraCtrl, cameraGlobalCtl);
	if(cameraGlobalCtl.cameraCount == 0)
		return E_FAIL;
	
	return S_OK;
}

HRESULT CMightex_VideoShow::GetInterfaces(void)
{
    HRESULT hr;
	
	CoInitialize(NULL);
	
    // Create the filter graph
    hr = CoCreateInstance (CLSID_FilterGraph, NULL, CLSCTX_INPROC, 
		IID_IGraphBuilder, (void **) &g_pGraph);
    if (FAILED(hr))
        return hr;
	
/*	
    // Create the capture graph builder
    hr = CoCreateInstance (CLSID_CaptureGraphBuilder2 , NULL, CLSCTX_INPROC, 
		IID_ICaptureGraphBuilder2, (void **) &g_pCapture);
    if (FAILED(hr))
        return hr;

    hr = g_pGraph->QueryInterface(IID_IMediaEvent, (LPVOID *) &g_pME);
    if (FAILED(hr))
        return hr;

    hr = CoCreateInstance (CLSID_SystemClock, NULL, CLSCTX_INPROC, 
		IID_IReferenceClock, (void **) &g_pRC);
	if (FAILED(hr))
        return hr;
	
    hr = g_pGraph->QueryInterface(IID_IMediaFilter, (LPVOID *) &g_pMF);
    if (FAILED(hr))
        return hr;
	//g_pMF->SetSyncSource(g_pRC);
*/
    // Obtain interfaces for media control and Video Window
    hr = g_pGraph->QueryInterface(IID_IMediaControl, (LPVOID *) &g_pMC);
    if (FAILED(hr))
        return hr;
	
    hr = g_pGraph->QueryInterface(IID_IVideoWindow, (LPVOID *) &g_pVW);
    if (FAILED(hr))
        return hr;

    hr = CoCreateInstance (CLSID_Mightex_BufferCCDSource, NULL, CLSCTX_INPROC_SERVER, 
		IID_IBaseFilter, reinterpret_cast<void**>(&pMightex_BufferCCDSourceFilter));
    if (FAILED(hr))
        return hr;
	
    hr = CoCreateInstance(CLSID_VideoRenderer, NULL, 
		CLSCTX_INPROC_SERVER, IID_IBaseFilter, 
		reinterpret_cast<void**>(&pVideoRendererFilter));
    if (FAILED(hr))
        return hr;

	hr = pMightex_BufferCCDSourceFilter->QueryInterface(IID_IMightex_BufferCCDSource, (void **)&mIMightex_BufferCCDSource);
    if (FAILED(hr))
        return hr;

	hr = pMightex_BufferCCDSourceFilter->QueryInterface(IID_IAMStreamConfig, (void **)&pSC);
    if (FAILED(hr))
        return hr;
	
	hr = CoCreateInstance (CLSID_SmartTee, NULL, CLSCTX_INPROC_SERVER, 
		IID_IBaseFilter, reinterpret_cast<void**>(&pSmartTee));
    if (FAILED(hr))
        return hr;

	hr = CoCreateInstance (CLSID_AviDest, NULL, CLSCTX_INPROC_SERVER, 
		IID_IBaseFilter, reinterpret_cast<void**>(&pAviDest));
    if (FAILED(hr))
        return hr;
	
	hr = CoCreateInstance (CLSID_FileWriter, NULL, CLSCTX_INPROC_SERVER, 
		IID_IBaseFilter, reinterpret_cast<void**>(&pFileWriter));
    if (FAILED(hr))
        return hr;
	
	hr = pFileWriter->QueryInterface(IID_IFileSinkFilter, (void **) &pFS);
    if (FAILED(hr))
        return hr;
	
	hr = pAviDest->QueryInterface(IID_IConfigInterleaving, (void **) &pConfigInterleaving);
    if (FAILED(hr))
        return hr;
	
	hr = pConfigInterleaving->put_Mode(INTERLEAVE_CAPTURE);
	if (FAILED(hr))
		return hr;
	/*	
	//hr = pAviDest->QueryInterface(IID_IConfigAviMux, (void **)&pConfigAviMux);
    //if (FAILED(hr))
    //    return hr;
	//pConfigAviMux->SetOutputCompatibilityIndex(TRUE);
	//hr = pConfigAviMux->SetMasterStream(0);
    //if (FAILED(hr))
    //    return hr;
	
    // enumerate first Audio capture devices
    ICreateDevEnum *pCreateDevEnum = 0;
    IEnumMoniker *pEm = 0;
    ULONG cFetched;
    IMoniker *pmAudio;
	
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER, 
		IID_ICreateDevEnum, (void**)&pCreateDevEnum);
    if (FAILED(hr))
        return hr;
    hr = pCreateDevEnum->CreateClassEnumerator(CLSID_AudioInputDeviceCategory, &pEm, 0);
    pCreateDevEnum->Release();
    if (FAILED(hr))
        return hr;
    pEm->Reset();
	
    hr = pEm->Next(1, &pmAudio, &cFetched);
    if (FAILED(hr))
        return hr;
	hr = pmAudio->BindToObject(0, 0, IID_IBaseFilter, (void**)&pACap);
    if (FAILED(hr))
        return hr;
*/	
    return S_OK;
}

/////////////////////////////////////////////////////////////////////////////
// This routine enumerates directshow compressors and adds them to a CStringList
/////////////////////////////////////////////////////////////////////////////

HRESULT CMightex_VideoShow::AddCompressorsToList(CStringList &m_CompressorList)
{
    HRESULT hr = 0;

	int compressorCount = 0;
	int validCompressorCount = 0;

	AM_MEDIA_TYPE *pmt;
	hr = pSC->GetFormat(&pmt);
	hr = g_pGraph->AddFilter(pAviDest, L"AVI Mux Filter");	
	
    // reset the list contents
    m_CompressorList.RemoveAll();
	
    // create an enumerator object
    CComPtr< ICreateDevEnum > pCreateDevEnum;
    hr = CoCreateInstance(
		CLSID_SystemDeviceEnum, 
		NULL, 
		CLSCTX_INPROC_SERVER,
		IID_ICreateDevEnum, 
		(void**) &pCreateDevEnum);
	
    if(FAILED(hr))
    {
        AfxMessageBox(TEXT("Failed to create system enumerator"));
        return hr;
    }
	
    // tell the enumerator to enumerate Video Compressors
    CComPtr< IEnumMoniker > pEm;
    hr = pCreateDevEnum->CreateClassEnumerator(
		CLSID_VideoCompressorCategory,
		&pEm, 
		0);
	
    if(FAILED(hr))
    {
        AfxMessageBox(TEXT("Failed to create class enumerator"));
        return hr;
    }
	
    // start enumerating at the beginning
    pEm->Reset();
	
    // Look for all Video Compressors and add them to the combo box.
    // Note that we do NOT alphabetize the compressors in the list,
    // because we expect them to be in the same order when the user selects
    // an item.  At that point, we will enumerate through the video compressors
    // again in the same order and select the requested item.
    while(1)
    {
        // Ask for the next VideoCompressor Moniker.
        // A Moniker represents an object, but is not the object itself.
        // You must get the object using the moniker's BindToObject
        // or you can get a "PropertyBag" by calling BindToStorage
        //
        ULONG cFetched = 0;
        CComPtr< IMoniker > pMoniker;
		
        hr = pEm->Next(1, &pMoniker, &cFetched);
        if(!pMoniker)
        {
            break;
        }
        
        // convert the Moniker to a PropertyBag, an object you can use to
        // ask the object's Name
        CComPtr< IPropertyBag > pBag;
		
        hr = pMoniker->BindToStorage(0, 0, IID_IPropertyBag, (void**) &pBag);

		CComPtr< IBaseFilter > temp_pCompressor;
		hr = pMoniker->BindToObject(0, 0, IID_IBaseFilter, (void**) &temp_pCompressor);
		
		hr = g_pGraph->AddFilter(temp_pCompressor, L"Compressor Filter");

		CComPtr<IPin> pCompressorIn = GetInPin(temp_pCompressor, 0);
		CComPtr<IPin> pCompressorOut0 = GetOutPin(temp_pCompressor, 0);
		CComPtr<IPin> pAviDestIn0 = GetInPin(pAviDest, 0);
		
		hr = pMightex_BufferCCDSourceFilterOut->Connect(pCompressorIn, pmt);
        if(!FAILED(hr))
			hr = g_pGraph->Connect(pCompressorOut0, pAviDestIn0);
			//hr = pCompressorOut0->Connect(pAviDestIn0, pmt);
		g_pGraph->RemoveFilter(temp_pCompressor);
		
        if(!FAILED(hr))
        {
			compressorNum[validCompressorCount++] = compressorCount;

            // each video compressor has a name, so ask for it
            VARIANT var;
            var.vt = VT_BSTR;
			
            hr = pBag->Read(L"FriendlyName",&var, NULL);
            if(hr == NOERROR)
            {
                USES_CONVERSION;
                TCHAR * tName = W2T(var.bstrVal);
                SysFreeString(var.bstrVal);
				
                // add the object's name to the list
                m_CompressorList.AddTail(tName);
            }
        }
		
		compressorCount++;
    }

	DeleteMediaType(pmt);
	g_pGraph->RemoveFilter(pAviDest);
	
    return (validCompressorCount > 0 ? S_OK : E_FAIL);
}

/////////////////////////////////////////////////////////////////////////////
// ask for the n'th compressor in the list and return a pointer to a
// DirectShow filter
/////////////////////////////////////////////////////////////////////////////

void CMightex_VideoShow::GetCompressor(int n, IBaseFilter ** ppCompressor)
{
	n = compressorNum[n];
	
    HRESULT hr = 0;
	
    if (!ppCompressor)
    {
        return;
    }
	
    *ppCompressor = 0;
	
    // we use the same technique in this routine as the one that
    // adds compressors to the UI list box, except this time we
    // return a pointer to an actual filter
	
    CComPtr< ICreateDevEnum > pCreateDevEnum;
    hr = CoCreateInstance(
		CLSID_SystemDeviceEnum, 
		NULL, 
		CLSCTX_INPROC_SERVER, 
		IID_ICreateDevEnum, 
		(void**) &pCreateDevEnum);
	
    if(FAILED(hr))
    {
        return;
    }
	
    CComPtr< IEnumMoniker > pEm;
    hr = pCreateDevEnum->CreateClassEnumerator(
		CLSID_VideoCompressorCategory, 
		&pEm, 
		0);
	
    if(FAILED(hr))
    {
        return;
    }
	
    pEm->Reset();
	
    while(1)
    {
        ULONG cFetched = 0;
        CComPtr< IMoniker > pMoniker;
		
        hr = pEm->Next(1, &pMoniker, &cFetched);
        if(!pMoniker)
        {
            break;
        }
		
        // if this is the object we wanted, then convert the Moniker
        // to an actual DirectShow filter by calling BindToObject on it
        //
        if(n == 0)
        {
            hr = pMoniker->BindToObject(0, 0, IID_IBaseFilter, (void**) ppCompressor);
            if(FAILED(hr))
            {
            }
            return;
        }
		
        n--;
    }
	
    return;
}

HRESULT 
CMightex_VideoShow::ConnectFilters(CComPtr<IGraphBuilder> graph_, CComPtr<IBaseFilter> pUpFilter, CComPtr<IBaseFilter> pDownFilter)
{
	
    if( !pUpFilter || !pDownFilter )
    {
        return E_INVALIDARG;
    }
	
    // All the need pin & pin enumerator pointers
    CComPtr<IEnumPins>  pEnumUpFilterPins , 
		pEnumDownFilterPins;
	
    CComPtr<IPin>   pUpFilterPin , 
		pDownFilterPin;
	
    HRESULT hr = S_OK;
	
    // Get the pin enumerators for both the filtera
    hr = pUpFilter->EnumPins(&pEnumUpFilterPins); 
    if( FAILED( hr ) )
    {
        return hr;
    }
	
    hr =  pDownFilter->EnumPins(&pEnumDownFilterPins); 
    if( FAILED( hr ) )
    {
        return hr;
    }
	
	
    // Loop on every pin on the Upstream Filter
    BOOL bConnected = FALSE;
    PIN_DIRECTION pinDir;
    ULONG nFetched = 0;
    while(pUpFilterPin.Release( ), S_OK == pEnumUpFilterPins->Next(1, &pUpFilterPin, &nFetched) )
    {
        // Make sure that we have the output pin of the upstream filter
        hr = pUpFilterPin->QueryDirection( &pinDir );
        if( FAILED( hr ) || PINDIR_INPUT == pinDir )
        {
            continue;
        }
		
        //
        // I have an output pin; loop on every pin on the Downstream Filter
        //
        while(pDownFilterPin.Release( ), S_OK == pEnumDownFilterPins->Next(1, &pDownFilterPin, &nFetched) )
        {
            hr = pDownFilterPin->QueryDirection( &pinDir );
            if( FAILED( hr ) || PINDIR_OUTPUT == pinDir )
            {
                continue;
            }
			
            // Try to connect them and exit if u can else loop more until you can
            if(SUCCEEDED(graph_->ConnectDirect(pUpFilterPin, pDownFilterPin, NULL)))
            {
                bConnected = TRUE;
                break;
            }
        }
		
        hr = pEnumDownFilterPins->Reset();
        if( FAILED( hr ) )
        {
            return hr;
        }
    }
	
    if( !bConnected )
    {
        return E_FAIL;
    }
	
    return S_OK;
}

HRESULT CMightex_VideoShow::ResizeVideoWindow(HWND ghApp)
{
    // Resize the video preview window to match owner window size
    if (g_pVW)
    {
        RECT rc;
        
        // Make the preview video fill our window
        GetClientRect(ghApp, &rc);
        g_pVW->SetWindowPosition(0, 0, rc.right, rc.bottom);
    }
	return S_OK;	
}

HRESULT CMightex_VideoShow::SetupVideoWindow(HWND ghApp)
{
    HRESULT hr;
	
    // Set the video window to be a child of the main window
    hr = g_pVW->put_Owner((OAHWND)ghApp);
    if (FAILED(hr))
        return hr;
    
    // Set video window style
    hr = g_pVW->put_WindowStyle(WS_CHILD | WS_CLIPCHILDREN);
    if (FAILED(hr))
        return hr;
	
    // Use helper function to position video window in client rect 
    // of main application window
    ResizeVideoWindow(ghApp);
	
    // Make the video window visible, now that it is properly positioned
    hr = g_pVW->put_Visible(OATRUE);
    if (FAILED(hr))
        return hr;
	
	return S_OK;	
}

HRESULT CMightex_VideoShow::Preview(HWND ghApp)
{
	if (isPreviewing) return S_OK;
	
    HRESULT hr;
	
	if (isCapturing) {

		if (MessageBox(ghApp, "Will it restart to capture?", "Alert!", MB_YESNO) == IDNO)
			return S_OK;
		
		g_pMC->Stop();
	}
	else
	{
		hr = ConnectFilters(g_pGraph, pMightex_BufferCCDSourceFilter, pSmartTee);
		if (FAILED(hr))
		{
			return hr;
		}
	}
		
	//if (isCapturing)
		hr = g_pGraph->Connect(pSmartTeeOut1, pVideoRendererFilterIn);
		//pSmartTeeOut = GetOutPin(pSmartTee, 1);
	//else
	//	hr = g_pGraph->Connect(pSmartTeeOut0, pVideoRendererFilterIn);
	if (FAILED(hr))
	{
		return hr;
	}
		
	if (old_ghApp != ghApp) {
		// Set video window style and position
		hr = SetupVideoWindow(ghApp);
		if (FAILED(hr))
		{
			return hr;
		}
		old_ghApp = ghApp;
	}

	// Start previewing video data
	hr = g_pMC->Run();
	if (FAILED(hr))
	{
		return hr;
	}
		
	isPreviewing = TRUE;
	
	SetWindowCaption();
	
	return S_OK;	
}

HRESULT CMightex_VideoShow::StopPreview()
{
	if (!isPreviewing) return S_OK;

	HRESULT hr;
	
	if (isCapturing) {		
		if (MessageBox(old_ghApp, "Will it restart to capture?", "Alert!", MB_YESNO) == IDNO)
			return S_OK;
	}	

	g_pMC->Stop();
	
	//if (isCapturing)
		hr = g_pGraph->Disconnect(pSmartTeeOut1);
	//else
	//	hr = g_pGraph->Disconnect(pSmartTeeOut0);	
	if (FAILED(hr))
	{
		return hr;
	}
		
	hr = g_pGraph->Disconnect(pVideoRendererFilterIn);
	if (FAILED(hr))
	{
		return hr;
	}
	
	isPreviewing = FALSE;
	
	if (isCapturing)
	{
		hr = g_pMC->Run();
		if (FAILED(hr))
		{
			return hr;
		}		
	}
	else
	{
		hr = g_pGraph->Disconnect(pSmartTeeIn);
		if (FAILED(hr))
		{
			return hr;
		}
		
		hr = g_pGraph->Disconnect(pMightex_BufferCCDSourceFilterOut);
		if (FAILED(hr))
		{
			return hr;
		}
	}
	
	return S_OK;	
}

HRESULT CMightex_VideoShow::Capture(WCHAR * targetFile, int compressorNum)
{	
	if (isCapturing) return S_OK;
	
    HRESULT hr;
	
	if (isPreviewing) 
		g_pMC->Stop();
	//else
	{
		//hr = ConnectFilters(g_pGraph, pMightex_BufferCCDSourceFilter, pSmartTee);
		//if (FAILED(hr))
		{
		//	return hr;
		}
	}
	
	hr = g_pGraph->Disconnect(pMightex_BufferCCDSourceFilterOut);
	if (FAILED(hr))
	{
		return hr;
	}
	
	hr = g_pGraph->Disconnect(pSmartTeeIn);
	if (FAILED(hr))
	{
		return hr;
	}
		
	hr = g_pGraph->Connect(pMightex_BufferCCDSourceFilterOut, pSmartTeeIn);
	if (FAILED(hr))
	{
		return hr;
	}

	if (targetFile)
	{
		hr = pFS->SetFileName(targetFile, NULL);
		if (FAILED(hr))
			return hr;
	}

    // Add Audio Capture filter to our graph.
    //hr = g_pGraph->AddFilter(pACap, L"Audio Capture filter");
    //if (FAILED(hr))
    {
    //   pACap->Release();
    //    return hr;
    }
	// Add AVI Mux filter to our graph.
	hr = g_pGraph->AddFilter(pAviDest, L"AVI Mux Filter");
	if (FAILED(hr))
	{
		pAviDest->Release();
		return hr;
	}
	// Add File Writer filter to our graph.
	hr = g_pGraph->AddFilter(pFileWriter, L"File Writer Filter");
	if (FAILED(hr))
	{
		pFileWriter->Release();
		return hr;
	}

	if (compressorNum > -1) {
		if(pCompressor) pCompressor->Release();
		GetCompressor(compressorNum, &pCompressor);
		isCompressing = TRUE;
	}
	else if (compressorNum == -2)
		isCompressing = TRUE;

	if (isCompressing) 
	{
		// Add Compressor filter to our graph.
		hr = g_pGraph->AddFilter(pCompressor, L"Compressor Filter");
		if (FAILED(hr))
		{
			pCompressor->Release();
			return hr;
		}
		
		CComPtr<IPin> pCompressorIn = GetInPin(pCompressor, 0);
		hr = g_pGraph->Connect(pSmartTeeOut0, pCompressorIn);
		if (FAILED(hr))
		{
			return hr;
		}
		
		hr = ConnectFilters(g_pGraph, pCompressor, pAviDest);
		if (FAILED(hr))
		{
			return hr;
		}
	}//isCompressing
	else
	{
		CComPtr<IPin> pAviDestIn0 = GetInPin(pAviDest, 0);
		hr = g_pGraph->Connect(pSmartTeeOut0, pAviDestIn0);			
		if (FAILED(hr))
		{
			return hr;
		}
	}

	//CComPtr<IPin> pACapOut = GetOutPin(pACap, 0);
	//CComPtr<IPin> pAviDestIn      = GetInPin(pAviDest, 1);
	//hr = g_pGraph->Connect(pACapOut, pAviDestIn);
	//if (FAILED(hr))
	{
	//	return hr;
	}

	hr = ConnectFilters(g_pGraph, pAviDest, pFileWriter);
	if (FAILED(hr))
	{
		return hr;
	}
	
	hr = g_pMC->Run();
	if (FAILED(hr))
	{
		return hr;
	}
	
	isCapturing = TRUE;

	return S_OK;	
}

HRESULT CMightex_VideoShow::StopCapture()
{
	if (!isCapturing) return S_OK;
	
    HRESULT hr;

	g_pMC->Stop();
	
	hr = g_pGraph->Disconnect(pSmartTeeOut0);
	if (FAILED(hr))
	{
		return hr;
	}

	hr = g_pGraph->RemoveFilter(pFileWriter);
	if (FAILED(hr))
	{
		return hr;
	}
	
	hr = g_pGraph->RemoveFilter(pAviDest);
	if (FAILED(hr))
	{
		return hr;
	}

	if (pCompressor) {
		hr = g_pGraph->RemoveFilter(pCompressor);
		if (FAILED(hr))
		{
			return hr;
		}
	}
	//hr = g_pGraph->RemoveFilter(pACap);
	//if (FAILED(hr))
	{
	//	return hr;
	}
	
	isCompressing = FALSE;
	isCapturing = FALSE;
	
	hr = g_pGraph->Disconnect(pSmartTeeIn);
	if (FAILED(hr))
	{
		return hr;
	}
	
	hr = g_pGraph->Disconnect(pMightex_BufferCCDSourceFilterOut);
	if (FAILED(hr))
	{
		return hr;
	}

	if (isPreviewing)
	{
		hr = g_pGraph->Disconnect(pSmartTeeOut1);
		if (FAILED(hr))
		{
			return hr;
		}

		hr = g_pGraph->Disconnect(pVideoRendererFilterIn);
		if (FAILED(hr))
		{
			return hr;
		}

		isPreviewing = FALSE;
		
		Preview(old_ghApp);
	}
	
	return S_OK;	
}

HRESULT CMightex_VideoShow::Snapshot(char * TargetFile, BOOL SavetoFileNeeded, BOOL SaveAsJPEG, BOOL AppendDataTime, BOOL SwitchSkipModeNeeded, int SaveFileCount, int SavedCount)
{
	strcpy(saveFileCtl.TargetFile, TargetFile);
	saveFileCtl.SavetoFileNeeded = SavetoFileNeeded;
	saveFileCtl.SaveAsJPEG = SaveAsJPEG;
	saveFileCtl.AppendDataTime = AppendDataTime;
	saveFileCtl.SwitchSkipModeNeeded = SwitchSkipModeNeeded;
	saveFileCtl.SaveFileCount = SaveFileCount;
	saveFileCtl.SavedCount = SavedCount;

	mIMightex_BufferCCDSource->Snapshot(TargetFile, SaveAsJPEG, AppendDataTime, SaveFileCount);

	return S_OK;
}

HRESULT CMightex_VideoShow::GetCameraControl(CCameraControl &cameraCtrl, CCameraGlobalControl &cameraGlobalCtl)
{
	mIMightex_BufferCCDSource->GetCameraControl(this->cameraCtrl, cameraGlobalCtl);
	cameraCtrl = this->cameraCtrl;
	cameraGlobalCtl = this->cameraGlobalCtl;
	return S_OK;
}

HRESULT CMightex_VideoShow::SetSelectCamera(int devID)
{
	mIMightex_BufferCCDSource->SetSelectCamera(devID);
	return S_OK;
}

HRESULT CMightex_VideoShow::SetWindowCaption()
{
	mIMightex_BufferCCDSource->GetPhysicalCameraFrameRate(cameraCtrl.actualFrameRate);

	double f_frameRate = 10000000.00 / cameraCtrl.streamFrameRate;
	char tempstr[16];
	sprintf(tempstr, "%.2f\0", f_frameRate);
	
	//WCHAR tempwstr[16];
	// Convert target filename
	//MultiByteToWideChar(CP_ACP, 0, tempstr, -1, 
	//	tempwstr, NUMELMS(tempwstr));
	
	char temp[6];
	sprintf(temp, "(1:%d)\0", cameraCtrl.bin + 1);
	if(!cameraCtrl.bin)
		*temp = '\0';
	
	WCHAR captionText[256];
	wsprintfW(captionText, L"Camera[%d] %dx%d%s (%d, %d) %d (%d, %d, %d) %s(%d)fps\0", 
		cameraCtrl.deviceID, cameraCtrl.width, cameraCtrl.height, temp,
		cameraCtrl.xStart, cameraCtrl.yStart, cameraCtrl.exposureTime * 50,
		cameraCtrl.redGain, cameraCtrl.greenGain, cameraCtrl.blueGain, 
		tempstr, 10000000 / cameraCtrl.actualFrameRate);
	
	g_pVW->put_Caption(captionText);
	return S_OK;
}

HRESULT CMightex_VideoShow::SetStreamFrameRate(LONGLONG frameRate)
{	
	if (cameraCtrl.streamFrameRate == frameRate) return S_OK;
	
	BOOL Capturing = isCapturing;
	BOOL Previewing = isPreviewing;
	
	if (isPreviewing)
		StopPreview();
	
	if (isCapturing) {
		if (MessageBox(old_ghApp, "Will it restart to capture?", "Alert!", MB_YESNO) == IDNO)
			return S_OK;
		StopCapture();
	}
	
	cameraCtrl.streamFrameRate = frameRate;
	mIMightex_BufferCCDSource->SetStreamFrameRate(frameRate);
		
	if (Previewing)
		Preview(old_ghApp);
	
	if (Capturing)
		Capture();
	
	SetWindowCaption();
	
	return S_OK;
}

HRESULT CMightex_VideoShow::SetCameraWorkMode(int WorkMode)
{
	HRESULT hr = mIMightex_BufferCCDSource->SetCameraWorkMode(WorkMode);
	if (hr == NOERROR)
		cameraCtrl.workMode = WorkMode;
	return S_OK;
}

HRESULT CMightex_VideoShow::SetResolution(int width, int height, int bin)
{
	if(cameraCtrl.width == width && cameraCtrl.height == height && cameraCtrl.bin == bin) return S_OK;
	
	BOOL Capturing = isCapturing;
	BOOL Previewing = isPreviewing;
	
	if (isCapturing) {
		if (MessageBox(old_ghApp, "Will it restart to capture?", "Alert!", MB_YESNO) == IDNO)
			return S_OK;
		StopCapture();
	}

	if (isPreviewing)
		StopPreview();

	HRESULT hr = mIMightex_BufferCCDSource->SetResolution(width, height, bin);
	if (hr == NOERROR)
	{
		cameraCtrl.width = width;
		cameraCtrl.height = height;
		cameraCtrl.bin = bin;
	}
	
	if (Previewing)
		Preview(old_ghApp);
	
	if (Capturing)
		Capture();

	SetWindowCaption();
	
	return S_OK;
}

HRESULT CMightex_VideoShow::SetExposureTime(int exposureTime)
{
	if(cameraCtrl.exposureTime == exposureTime) return S_OK;
	cameraCtrl.exposureTime = exposureTime;
	mIMightex_BufferCCDSource->SetExposureTime(exposureTime);
	if (!isPreviewing)
		mIMightex_BufferCCDSource->SetResolution(cameraCtrl.width, cameraCtrl.height, cameraCtrl.bin);
	
	SetWindowCaption();
	
	return S_OK;
}

HRESULT CMightex_VideoShow::SetGains(int redGain, int greenGain, int blueGain)
{
	if(cameraCtrl.redGain == redGain && cameraCtrl.greenGain == greenGain && cameraCtrl.blueGain == blueGain) return S_OK;
	cameraCtrl.redGain = redGain;
	cameraCtrl.greenGain = greenGain;
	cameraCtrl.blueGain = blueGain;
	mIMightex_BufferCCDSource->SetGains(redGain, greenGain, blueGain);

	SetWindowCaption();

	return S_OK;
}

HRESULT CMightex_VideoShow::SetXYStart(int xStart, int yStart)
{
	if(cameraCtrl.xStart == xStart && cameraCtrl.yStart == yStart) return S_OK;
	cameraCtrl.xStart = xStart;
	cameraCtrl.yStart = yStart;
	mIMightex_BufferCCDSource->SetXYStart(xStart, yStart);

	SetWindowCaption();

	return S_OK;
}

HRESULT CMightex_VideoShow::OpenPropertyPages(HWND ghApp)
{
	HRESULT hr;
	ISpecifyPropertyPages *pSpec;
	CAUUID cauuid;
	
	hr = pMightex_BufferCCDSourceFilter->QueryInterface(IID_ISpecifyPropertyPages,(void **)&pSpec);
	if(hr == S_OK)
	{
		hr = pSpec->GetPages(&cauuid);
		
		if(hr == S_OK)
			hr = OleCreatePropertyFrame(ghApp, 30, 30, NULL, 1,
				(IUnknown **)&pMightex_BufferCCDSourceFilter, cauuid.cElems,
				(GUID *)cauuid.pElems, 0, 0, NULL);
		
		CoTaskMemFree(cauuid.pElems);
		pSpec->Release();
	}
	
	return hr;
}