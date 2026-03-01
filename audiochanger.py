import tkinter as tk
import subprocess
import platform
import os
import sys
from pycaw.pycaw import AudioUtilities

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x300")
        self.root.configure(bg='#2e2e2e')
        
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 
        else:
            try: self.root.attributes('-type', 'utility')
            except: pass

        self.label = tk.Label(root, text="SELECT AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 9, 'bold'))
        self.label.pack(pady=10)

        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.refresh_ui()

    def get_audio_sinks(self):
        sinks = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                # ... (Standard Linux parsing logic here) ...
            
            elif platform.system() == "Windows":
                # PURE PYTHON: No PowerShell, no WMIC, no lag.
                devices = AudioUtilities.GetAllDevices()
                for device in devices:
                    # State 1 = Active/Plugged in
                    if device.State == 1:
                        sinks.append({
                            "id": device.FriendlyName, 
                            "name": device.FriendlyName, 
                            "active": False 
                        })
        except Exception as e:
            print(f"Error: {e}")
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            
            # 0x08000000 = CREATE_NO_WINDOW
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        # Only rebuild UI if the number of devices changed (prevents flickering)
        if len(new_devices) != len(self.current_devices):
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            for dev in new_devices:
                btn = tk.Button(
                    self.button_frame, 
                    text=f"🔊 {dev['name']}",
                    command=lambda d=dev['id']: self.switch_audio(d),
                    bg='#404040', fg='white', relief='flat', anchor='w', padx=10
                )
                btn.pack(fill='x', padx=10, pady=2)
            self.current_devices = new_devices
        
        # Check every 5 seconds (plenty for a startup app)
        self.root.after(5000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

