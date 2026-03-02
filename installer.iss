[Setup]
AppName=Audio Switcher
AppVersion=1.0
DefaultDirName={autopf}\AudioSwitcher
DefaultGroupName=Audio Switcher
OutputDir=dist
OutputBaseFilename=AudioSwitcherInstaller
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
; --- ADD THIS LINE TO SET THE INSTALLER ICON ---
SetupIconFile=app_icon.ico

[Files]
Source: "dist\audiochanger.exe"; DestDir: "{app}"; Flags: ignoreversion
; --- ADD THIS LINE TO INCLUDE THE ICON IN THE INSTALL FOLDER ---
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; --- ADD IconFilename TO THESE LINES TO SET THE DESKTOP/START ICONS ---
Name: "{autodesktop}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\audiochanger.exe"; Description: "Launch Audio Switcher"; Flags: nowait postinstall skipifsilent
