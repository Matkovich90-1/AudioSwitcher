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

[Files]
; This tells the installer to include your exe
Source: "dist\audiochanger.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Creates the desktop shortcut
Name: "{autodesktop}\Audio Switcher"; Filename: "{app}\audiochanger.exe"
; Creates a Start Menu shortcut
Name: "{group}\Audio Switcher"; Filename: "{app}\audiochanger.exe"

[Run]
; Option to launch right after installing
Filename: "{app}\audiochanger.exe"; Description: "Launch Audio Switcher"; Flags: nowait postinstall skipifsilent
