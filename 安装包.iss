; OpenCV 图片处理 —— Windows 安装包（Inno Setup 6）
; 编译：ISCC.exe 安装包.iss
; 依赖：先执行 PyInstaller 构建，产物在 .\dist\OpenCV图片处理\
; 相对路径都以本脚本所在目录为准

#define AppName "OpenCV 图片处理"
#define AppVersion "1.0.0"
#define AppExe "OpenCV图片处理.exe"
#define SrcDir "dist\OpenCV图片处理"

[Setup]
AppId={{3C7A1E64-9B25-4F8D-A1C3-6E2F5B908D47}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=本地工具
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\OpenCV图片处理
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=图片处理-安装包-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 打包出来的是 64 位程序
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=app.ico

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："

[Files]
; PyInstaller 的 onedir 产物整体装到安装目录
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
; 桌面（可选）
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "立即运行 {#AppName}"; Flags: nowait postinstall skipifsilent
