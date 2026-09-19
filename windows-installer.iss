; Windows installer for OpenCV Image Tool — Inno Setup 6
;
; Build:  ISCC.exe windows-installer.iss
; Needs:  run PyInstaller first so that .\dist\OpenCV Image Tool\ exists
; Paths:  all relative paths are resolved against this script's directory

#define AppName "OpenCV Image Tool"
; Version default. Can be overridden from the command line so it can be
; taken straight from main.py and never drift from the app's own version.
#ifndef AppVersion
  #define AppVersion "1.0.7"
#endif
#define AppExe "OpenCV Image Tool.exe"
#define SrcDir "dist\OpenCV Image Tool"

[Setup]
AppId={{3C7A1E64-9B25-4F8D-A1C3-6E2F5B908D47}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=evan-rio
AppPublisherURL=https://github.com/evan-rio/image-tool
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\OpenCV Image Tool
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=image-tool-{#AppVersion}-windows-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 64-bit only
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=app.ico

[Languages]
; The installer picks whichever of these matches the user's system language.
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; The whole PyInstaller onedir output goes into the application directory.
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
