# 🔊 Audio Switcher vx.x.x

A lightweight, cross-platform tool to quickly switch audio output devices. 
Designed specifically to bypass "locked" settings on unactivated Windows 11 systems and work natively on Pop!_OS/Debian.

## 📥 Downloads

**Get the latest version from the [Releases](https://github.com/Matkovich90-1/AudioSwitcher/releases) page.**

---

## 🪟 Windows Installation
1. Download `AudioSwitcherInstaller.exe`.
2. Run the installer. 
   - **Note:** Because this app is "unsigned," Windows SmartScreen will show a blue warning. Click **"More info"** and then **"Run anyway"**.
3. Use the **Desktop Shortcut** to launch.
4. Click **"🔄 REFRESH DEVICES"** to see your speakers/headphones.

## 🐧 Linux (Pop!_OS / Debian)
1. Download the `audiochanger` binary.
2. Make it executable:
   ```bash
   chmod +x audiochanger
3. Run it: ./audiochanger

 Requires wireplumber



 🛠️ How it Works
    Windows: Uses NirCmd and PowerShell to force audio switching without needing the Windows Settings app.
    
    Linux: Uses wpctl (PipeWire) for native, lag-free switching.
   
