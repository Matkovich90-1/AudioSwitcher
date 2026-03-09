[Setup]
; --- THE UPDATER LOCK (DO NOT CHANGE THIS ID IN FUTURE VERSIONS) ---
AppId={{A1B2C3D4-E5F6-4G7H-8I9J-K0L1M2N3O4P5}}
AppName=Audio Switcher
AppVersion=1.0.2
DefaultDirName={autopf}\AudioSwitcher
DefaultGroupName=Audio Switcher
OutputDir=dist
OutputBaseFilename=AudioSwitcherInstaller
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
CloseApplications=yes
SetupIconFile=installer_icon.ico

[Files]
Source: "dist\audiochanger.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\audiochanger.exe"; Description: "Launch Audio Switcher"; Flags: nowait postinstall skipifsilent
