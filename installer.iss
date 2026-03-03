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
; This sets the icon for the Installer/Setup .exe file
SetupIconFile=installer_icon.ico

[Files]
; The actual program built by PyInstaller
Source: "dist\audiochanger.exe"; DestDir: "{app}"; Flags: ignoreversion
; The app icon needs to be copied to the install folder so the shortcuts can find it
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop Shortcut - specifically using the app_icon.ico
Name: "{autodesktop}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"
; Start Menu Shortcut
Name: "{group}\Audio Switcher"; Filename: "{app}\audiochanger.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
; Option to launch the app immediately after the installer finishes
Filename: "{app}\audiochanger.exe"; Description: "Launch Audio Switcher"; Flags: nowait postinstall skipifsilent
