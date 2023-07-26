Imports System
Imports System.Windows.Forms
Imports System.Runtime.InteropServices

Public Class frmMain
    Public WinHwnd As IntPtr
    Public GrabStart As Integer

    Protected Overrides Sub WndProc(ByRef m As Message)
        Dim myBMP As Bitmap
        If m.Msg = &H401 Then
            If GrabStart = 1 Then
                FrameInfoLabel.Text = "Brightest pixel: " & BrightestPixel & vbCr & "Frames: " & FrameCount
                'We hard coded here, user might set the Bitmap size according to the ImageProperty.
                myBMP = New Bitmap(1392, 1040, 3 * 1392, System.Drawing.Imaging.PixelFormat.Format24bppRgb, _pImage)

                PBImage.Image = myBMP
            End If
        Else
            MyBase.WndProc(m)
        End If
    End Sub
    Private Sub Button1_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles Button1.Click
        WinHwnd = Me.Handle
        GrabStart = 1
        CameraSTART()
    End Sub

    Private Sub Button2_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles Button2.Click
        GrabStart = 0
        CameraSTOP()
    End Sub

    Private Sub frmMain_FormClosed(ByVal sender As System.Object, ByVal e As System.Windows.Forms.FormClosedEventArgs) Handles MyBase.FormClosed
        If _pImage <> IntPtr.Zero Then
            Marshal.FreeHGlobal(_pImage)
        End If
    End Sub
End Class
