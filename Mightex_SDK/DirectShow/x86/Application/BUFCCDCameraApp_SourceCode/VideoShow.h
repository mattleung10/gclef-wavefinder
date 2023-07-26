//------------------------------------------------------------------------------
// File: videoShow.h
//
// Desc: DirectShow code - Video privewing and capturing.
//
// Copyright (c) Mightex Corporation.  All rights reserved.
//------------------------------------------------------------------------------

#pragma once

#ifndef __Mightex_VideoShow_DEFINED
#define __Mightex_VideoShow_DEFINED

#include <atlbase.h>
#include <dshow.h>
#include "dshowutil.h"
#include <streams.h>

enum eDEVICETYPE {ICX424M, ICX424C, ICX205AL, ICX205AK, ICX285AL, ICX285AQ, ICX445AL, ICX445AQ, ICX274AL, ICX274AQ};

const int MAX_RESOLUTIONS = 15;
const int MAX_RESOLUTIONS_V032 = 3;  
const int MAX_RESOLUTIONS_M001 = 13;
const int MAX_RESOLUTIONS_T001 = 14;
const int MAX_RESOLUTIONS_P001 = 15;
const int MAX_EXPOSURETIME[]={5, 10, 100, 750};
const int DEFAULT_WIDTH = 640;
const int DEFAULT_HEIGHT = 480;

/********************************************** 
 * 
 *  struct declarations
 * 
 **********************************************/

struct IMightex_BufferCCDSource;

static struct { int width; int height; }
s_vidFrameSize[] = 
{
	{  640,  120},
	{  640,  160},
	{  640,  240}, 
	{  640,  480}, 
	{ 1280,  240},
	{ 1392,  256}, 
	{ 1280,  320},
	{ 1392,  344}, 
	{ 1616,  308}, 
	{ 1280,  480},
	{ 1616,  410}, 
	{ 1392,  520}, 
	{ 1616,  616}, 
	{ 1280,  960},
	{ 1392, 1040}, 
	{ 1616, 1232}, 
};


static struct { int width; int height;}
frameSize_ICX424[] =
{
	{  640,  480}, 	
	{  320,  240}, 
	{  212,  160},
	{  160,  120},
};

static struct { int width; int height;}
frameSize_ICX445[] =
{
	{ 1280,  960},
	{  640,  480}, 	
	{  424,  320},
	{  320,  240}, 
};

static struct { int width; int height;}
frameSize_ICX205[] =
{
	{  1392, 1040}, 	
	{  696,  520}, 
	{  464,  344},
	{  348,  256},
};

static struct { int width; int height;}
frameSize_ICX274[] =
{
	{  1616, 1232}, 	
	{  808,  616}, 
	{  538,  410},
	{  404,  308},
};

struct CGrabFrameToFileCtl
{
	char TargetFile[256];
	BOOL SavetoFileNeeded;
	BOOL SaveAsJPEG;
	BOOL AppendDataTime;
	BOOL SwitchSkipModeNeeded;
	int SaveFileCount;
	int SavedCount;
};

struct CCameraControl
{
	char ModuleNo[32];
	char SerialNo[32];
	eDEVICETYPE DeviceType;
	int deviceID;
	int workMode;
	int bin;
	int width;
	int height;
	int MAX_RESOLUTION;
	int exposureTime;
	int xStart;
	int	yStart;
	int redGain;
	int greenGain;
	int blueGain;
	LONGLONG streamFrameRate;
	LONGLONG actualFrameRate;
};

struct CCameraGlobalControl
{
	int cameraCount;
	char camNames[8][48];
	int Gamma;
	int Contrast;
	int Brightness;
	int Sharpness;
	int BWMode;
	int H_Mirror;
	int V_Flip;
};

/********************************************** 
 * 
 *  Class declarations
 * 
 **********************************************/

class CMightex_VideoShow
{
	IVideoWindow  * g_pVW;
	IMediaControl * g_pMC;
	IGraphBuilder * g_pGraph;
	//IMediaEventEx * g_pME;
	//ICaptureGraphBuilder2 * g_pCapture;
	//IReferenceClock * g_pRC;
	//IMediaFilter * g_pMF;
    IBaseFilter * pMightex_BufferCCDSourceFilter;
	IMightex_BufferCCDSource * mIMightex_BufferCCDSource;
	IBaseFilter * pVideoRendererFilter;
	IBaseFilter * pSmartTee;
	IBaseFilter * pCompressor;
	IBaseFilter * pAviDest;
	IConfigInterleaving * pConfigInterleaving;
	//IConfigAviMux * pConfigAviMux;
    //IBaseFilter * pACap;
	IBaseFilter * pFileWriter;
    IFileSinkFilter * pFS;
	IAMStreamConfig * pSC;
	CComPtr<IPin> pSmartTeeOut0;
	CComPtr<IPin> pSmartTeeOut1;
	CComPtr<IPin> pSmartTeeIn;
	CComPtr<IPin> pVideoRendererFilterIn;
	CComPtr<IPin> pMightex_BufferCCDSourceFilterOut;

	HWND old_ghApp;
	BOOL isPreviewing;
	BOOL isCapturing;
	BOOL isCompressing;
	CGrabFrameToFileCtl saveFileCtl;
	CCameraControl cameraCtrl;
	CCameraGlobalControl cameraGlobalCtl;
	int compressorNum[256];
	
	HRESULT InitCameraControl();
	HRESULT GetInterfaces(void);
	void GetCompressor(int n, IBaseFilter ** ppCompressor);
	HRESULT ConnectFilters(CComPtr<IGraphBuilder> graph_, CComPtr<IBaseFilter> pUpFilter, CComPtr<IBaseFilter> pDownFilter);
	HRESULT ResizeVideoWindow(HWND ghApp);
	HRESULT SetupVideoWindow(HWND ghApp);
	
public:

    CMightex_VideoShow();
    ~CMightex_VideoShow();

	HRESULT Init();
	HRESULT AddCompressorsToList(CStringList &m_CompressorList);
	HRESULT Preview(HWND ghApp = NULL);
	HRESULT StopPreview();
	HRESULT Capture(WCHAR * targetFile = NULL, int compressorNum = -2);
	HRESULT StopCapture();
	HRESULT Snapshot(char * TargetFile, BOOL SavetoFileNeeded, BOOL SaveAsJPEG, BOOL AppendDataTime, BOOL SwitchSkipModeNeeded, int SaveFileCount, int SavedCount);
	BOOL GetPreviewState()	{ return isPreviewing; }
	BOOL GetCaptureState()	{ return isCapturing; }
	HRESULT GetCameraControl(CCameraControl &cameraCtrl, CCameraGlobalControl &cameraGlobalCtl);
	HRESULT SetSelectCamera(int devID);
	HRESULT SetStreamFrameRate(LONGLONG frameRate);
	HRESULT SetCameraWorkMode(int WorkMode);
	HRESULT SetResolution(int width, int height, int bin);
	HRESULT SetExposureTime(int exposureTime);
	HRESULT SetGains(int redGain, int greenGain, int blueGain);
	HRESULT SetXYStart(int xStart, int yStart);
	HRESULT OpenPropertyPages(HWND ghApp);		
	HRESULT SetWindowCaption();
};

#endif