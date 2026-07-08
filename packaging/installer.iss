; ============================================================
;  installer.iss - Inno Setup script cho PeiPei Clone Voice
;  Goi thu muc release\ thanh 1 file Setup.exe chuyen nghiep.
;
;  Build: chay build.bat (ra release\) -> roi chay packaging\build_installer.bat
;         (hoac mo file nay bang Inno Setup va bam Compile).
;  Output: build\PeiPeiCloneVoice_Setup.exe
; ============================================================

#define MyAppName "PeiPei Clone Voice"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "PeiPei"
#define MyAppExe "run.bat"
#define IconRel "..\release\icon.ico"

[Setup]
; AppId co dinh (dung de nhan dien khi nang cap/go cai). KHONG doi GUID nay.
AppId={{8F3A1C24-5B6D-4E91-A2F7-9C0D3E5B71A4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Cai PER-USER (khong can quyen Admin) vao %LOCALAPPDATA%\Programs\... -> thu muc
; GHI DUOC (app tu cai torch + tai model vao day). KHONG cai vao Program Files.
PrivilegesRequired=lowest
DefaultDirName={autopf}\PeiPeiCloneVoice
DisableProgramGroupPage=yes
OutputDir=..\build
OutputBaseFilename=PeiPeiCloneVoice_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
#if FileExists(IconRel)
SetupIconFile={#IconRel}
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong ngoai Desktop"; GroupDescription: "Bieu tuong:"

[Files]
; Lay TOAN BO thu muc release\ (python nhung + app.pyd + main.py + run.bat + setup.bat + ...)
Source: "..\release\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{autoprograms}\Huong dan su dung"; Filename: "{app}\HUONG_DAN_KHACH.txt"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
; Hoi mo app ngay sau khi cai (lan dau app tu cai deps + tai model).
Filename: "{app}\{#MyAppExe}"; Description: "Mo PeiPei Clone Voice ngay"; Flags: nowait postinstall skipifsilent shellexec

[InstallDelete]
; Khi CAI DE (update): xoa moc .setup_done -> lan chay sau setup.bat tu kiem lai deps
; (torch/model da co san -> pip chi kiem nhanh + cai THEM lib moi neu ban update can).
; KHONG xoa torch/model/user_data -> giu nguyen, khach khong phai tai lai vai GB.
Type: files; Name: "{app}\.setup_done"

[UninstallDelete]
; Khi GO CAI: xoa cac thu nang TU SINH (deps + model) cho sach. GIU user_data (giong da tao).
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\python"
Type: files; Name: "{app}\.setup_done"
