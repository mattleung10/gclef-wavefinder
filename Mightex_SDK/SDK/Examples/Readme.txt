VC and Delphi examples use the "XXX_XXXUSBCamera_SDK.DLL" which is based on "cdecl" calling convention, 
for VB, VB.net and C# examples, they should use "XXX_XXXUSBCamera_SDK_Stdcall.dll", which is based on "stdcall" convention,
Currently, the libraries in each sample is x86 library (32bit).
Note that when using those samples as 64bit applications, user should use the libraries of 64bit (x64) instead
of the those of 32bit (x86).
