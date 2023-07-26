object MainForm: TMainForm
  Left = 166
  Top = 63
  Width = 688
  Height = 495
  Caption = 'MainForm'
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  OldCreateOrder = False
  OnClose = FormClose
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object RzPanel1: TRzPanel
    Left = 0
    Top = 0
    Width = 680
    Height = 41
    Align = alTop
    BorderOuter = fsGroove
    TabOrder = 0
    object DevicesComboBox: TComboBox
      Left = 528
      Top = 4
      Width = 145
      Height = 21
      ItemHeight = 13
      TabOrder = 0
      Text = 'DevicesComboBox'
      OnChange = DevicesComboBoxChange
    end
    object ReSelectDeviceBitBtn: TBitBtn
      Left = 488
      Top = 4
      Width = 29
      Height = 29
      TabOrder = 1
      OnClick = ReSelectDeviceBitBtnClick
      Glyph.Data = {
        42010000424D4201000000000000760000002800000011000000110000000100
        040000000000CC00000000000000000000001000000010000000000000000000
        BF0000BF000000BFBF00BF000000BF00BF00BFBF0000C0C0C000808080000000
        FF0000FF000000FFFF00FF000000FF00FF00FFFF0000FFFFFF00777777777777
        7777700000007777777777777777700000007000000007777777700000007FFF
        FFFF07777777700000007FFFFFFF07777777700000007FFFFFFF077777777000
        00007000000000007747700000007EFEFEFEFEF07744700000007FEFEFEFEFE0
        4444400000007EFEFEFEFEF07744700000007000000000007747700000007FFF
        FFFF07777777700000007FFFFFFF07777777700000007FFFFFFF077777777000
        0000700000000777777770000000777777777777777770000000777777777777
        777770000000}
    end
    object ShowFactoryPanelBitBtn: TBitBtn
      Left = 458
      Top = 4
      Width = 27
      Height = 29
      TabOrder = 2
      OnClick = ShowFactoryPanelBitBtnClick
      Glyph.Data = {
        66010000424D6601000000000000760000002800000014000000140000000100
        040000000000F000000000000000000000001000000010000000000000000000
        BF0000BF000000BFBF00BF000000BF00BF00BFBF0000C0C0C000808080000000
        FF0000FF000000FFFF00FF000000FF00FF00FFFF0000FFFFFF00777777777777
        7777777700007777777778888877777700007777777000008887777700007777
        77ECCCCC088777770000777777EC6EEC088777770000777777EC08EC08877777
        0000777777EC006C088777770000777777ECCCCC088777770000777777ECCCCC
        088877770000777777ECCCCC08888777000077777CCCCCCCC088887700007777
        CCCCCCCCCC0888870000777CCCCCCCCCCCC08887000077ECCCCCCCCCCCCC0887
        000077ECCCC0877ECCCC0887000077ECCC088777ECCC0877000077ECCC088777
        ECCC07770000777ECC077777ECC0777700007777EE677777EE67777700007777
        77777777777777770000}
    end
    object ShowImageButton: TBitBtn
      Left = 6
      Top = 8
      Width = 85
      Height = 25
      Caption = 'Start Grab'
      TabOrder = 3
      OnClick = ShowImageButtonClick
    end
  end
  object RzPanel2: TRzPanel
    Left = 0
    Top = 41
    Width = 680
    Height = 414
    Align = alClient
    BorderOuter = fsGroove
    TabOrder = 1
    object Label1: TLabel
      Left = 144
      Top = 128
      Width = 17
      Height = 13
      Caption = '(us)'
    end
    object Label2: TLabel
      Left = 8
      Top = 168
      Width = 35
      Height = 13
      Caption = 'XStart :'
    end
    object Label3: TLabel
      Left = 8
      Top = 200
      Width = 38
      Height = 13
      Caption = 'YStart : '
    end
    object Label4: TLabel
      Left = 8
      Top = 272
      Width = 33
      Height = 13
      Caption = 'RGain:'
    end
    object Label5: TLabel
      Left = 8
      Top = 304
      Width = 33
      Height = 13
      Caption = 'GGain:'
    end
    object Label6: TLabel
      Left = 8
      Top = 336
      Width = 32
      Height = 13
      Caption = 'BGain:'
    end
    object StatusBar1: TStatusBar
      Left = 2
      Top = 386
      Width = 676
      Height = 26
      Panels = <
        item
          Width = 120
        end
        item
          Width = 160
        end
        item
          Width = 80
        end
        item
          Width = 80
        end
        item
          Width = 80
        end
        item
          Width = 80
        end
        item
          Width = 80
        end
        item
          Width = 50
        end>
      SimplePanel = False
    end
    object SetToNormalModeButton: TButton
      Left = 8
      Top = 8
      Width = 137
      Height = 25
      Caption = 'Set To Normal Mode'
      TabOrder = 1
      OnClick = SetToNormalModeButtonClick
    end
    object SetToTriggerModeButton: TButton
      Left = 8
      Top = 40
      Width = 137
      Height = 25
      Caption = 'Set To Trigger Mode'
      TabOrder = 2
      OnClick = SetToTriggerModeButtonClick
    end
    object SetExposureTimeButton: TButton
      Left = 176
      Top = 120
      Width = 137
      Height = 25
      Caption = 'Set Exposure Time'
      TabOrder = 3
      OnClick = SetExposureTimeButtonClick
    end
    object ExposureTimeEdit: TEdit
      Left = 16
      Top = 122
      Width = 121
      Height = 21
      TabOrder = 4
      Text = '1000'
    end
    object ResolutionComboBox: TComboBox
      Left = 16
      Top = 88
      Width = 145
      Height = 21
      ItemHeight = 13
      TabOrder = 5
      Text = 'ResolutionComboBox'
      Items.Strings = (
        '348 x 256'
        '464 x 344'
        '696 x 520'
        '1392 x 1040')
    end
    object XStartEdit: TEdit
      Left = 64
      Top = 160
      Width = 65
      Height = 21
      TabOrder = 6
      Text = '0'
    end
    object YStartEdit: TEdit
      Left = 64
      Top = 192
      Width = 65
      Height = 21
      TabOrder = 7
      Text = '0'
    end
    object SetXYStartButton: TButton
      Left = 152
      Top = 188
      Width = 97
      Height = 25
      Caption = 'Set XY Start'
      TabOrder = 8
      OnClick = SetXYStartButtonClick
    end
    object RedGainEdit: TEdit
      Left = 48
      Top = 264
      Width = 49
      Height = 21
      TabOrder = 9
      Text = '8'
    end
    object GreenGainEdit: TEdit
      Left = 48
      Top = 296
      Width = 49
      Height = 21
      TabOrder = 10
      Text = '8'
    end
    object BlueGainEdit: TEdit
      Left = 48
      Top = 328
      Width = 49
      Height = 21
      TabOrder = 11
      Text = '8'
    end
    object SetGainButton: TButton
      Left = 128
      Top = 324
      Width = 97
      Height = 25
      Caption = 'Set Gains'
      TabOrder = 12
      OnClick = SetGainButtonClick
    end
    object SetResolutionButton: TButton
      Left = 176
      Top = 88
      Width = 105
      Height = 25
      Caption = 'Set Resolution'
      TabOrder = 13
      OnClick = SetResolutionButtonClick
    end
    object Button1: TButton
      Left = 128
      Top = 352
      Width = 153
      Height = 25
      Caption = 'Capture Current Frame'
      TabOrder = 14
      OnClick = Button1Click
    end
    object GetCurrentFrameButton: TButton
      Left = 288
      Top = 352
      Width = 137
      Height = 25
      Caption = 'Get Current Frames'
      TabOrder = 15
      OnClick = GetCurrentFrameButtonClick
    end
  end
end
