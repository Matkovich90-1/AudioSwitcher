import tkinter as tk
import subprocess
import platform
import os
import sys
import re

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x400")
        self.root.configure(bg='#2e2e2e')
        
        # OS-Specific Window Styling
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 
        else:
            try:
                self.root.attributes('-type', 'utility')
            except:
                pass

        self.label = tk.Label(root, text="SELECT AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 10, 'bold'))
        self.label.pack(pady=15)

        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.refresh_ui()

    def get_audio_sinks(self):
        sinks = []
        try:
            # --- LINUX SIDE (PipeWire / Pop!_OS) ---
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    parts = result.stdout.split("Sinks:")
                    sinks_section = parts[1].split("Sink endpoints:")[0]
                    for line in sinks_section.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            node_id = match.group(1)
                            name = re.split(r'\[', match.group(2))[0].strip()
                            sinks.append({"id": node_id, "name": name, "active": "*" in line})
            
            # --- WINDOWS SIDE (Direct Registry Scan) ---
            elif platform.system() == "Windows":
                import winreg
                # The registry key where Windows stores all audio endpoint data
                base_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
                try:
                    reg_root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path)
                    for i in range(winreg.QueryInfoKey(reg_root)[0]):
                        device_guid = winreg.EnumKey(reg_root, i)
                        # Properties subkey contains the actual device name
                        prop_path = f"{base_path}\\{device_guid}\\Properties"
                        try:
                            prop_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, prop_path)
                            for j in range(winreg.QueryInfoKey(prop_key)[1]):
                                val_name, val_data, _ = winreg.EnumValue(prop_key, j)
                                # This specific GUID is the standard Windows "Friendly Name" property
                                if "{b725f130-4752-47bf-af2d-e2805c3d27a4},2" in val_name:
                                    sinks.append({"id": val_data, "name": val_data, "active": False})
                        except: continue
                except: pass
        except Exception as e:
            print(f"Error: {e}")
        return sinks

    def switch_audio(self, device_name):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_name])
        elif platform.system() == "Windows":
            # Find the bundled nircmd.exe inside the onefile exe
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            # 0x08000000 = CREATE_NO_WINDOW (Stealth mode)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_name, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_name, "2"], creationflags=0x08000000)
        
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        # Only redraw if the number of devices changes (prevents flickering)
        if len(new_devices) != len(self.current_devices):
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            if not new_devices:
                tk.Label(self.button_frame, text="No devices found", bg='#2e2e2e', fg='gray').pack()
            else:
                for dev in new_devices:
                    icon = "✅ " if dev['active'] else "🔊 "
                    bg_color = '#1e88e5' if dev['active'] else '#404040'
                    
                    btn = tk.Button(
                        self.button_frame, 
                        text=f"{icon}{dev['name']}",
                        command=lambda d=dev['id']: self.switch_audio(d),
                        bg=bg_color, fg='white', relief='flat', anchor='w', padx=10,
                        font=('Sans', 9)
                    )
                    btn.pack(fill='x', padx=15, pady=3)
            self.current_devices = new_devices
        
        # Check every 5 seconds
        self.root.after(5000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
