import tkinter as tk
import subprocess
import platform
import os
import sys
import comtypes
from pycaw.pycaw import AudioUtilities
from pycaw.constants import AudioEndpoints, DEVICE_STATE

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x350")
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
                # ... (Standard Linux logic) ...
            
            elif platform.system() == "Windows":
                # CRITICAL: Initialize COM for this thread
                comtypes.CoInitialize()
                
                # Get all active playback (Output) devices
                devices = AudioUtilities.GetAllDevices()
                for device in devices:
                    # Filter for active devices only
                    if device.State == DEVICE_STATE.ACTIVE.value:
                        sinks.append({
                            "id": device.FriendlyName, 
                            "name": device.FriendlyName, 
                            "active": False 
                        })
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if platform.system() == "Windows":
                comtypes.CoUninitialize()
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            # Path handling for the bundled nircmd.exe
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            
            # 0x08000000 = CREATE_NO_WINDOW
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        
        # Rebuild if device list changed
        if len(new_devices) != len(self.current_devices):
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            for dev in new_devices:
                btn = tk.Button(
                    self.button_frame, 
                    text=f"🔊 {dev['name']}",
                    command=lambda d=dev['id']: self.switch_audio(d),
                    bg='#404040', fg='white', relief='flat', anchor='w', padx=10,
                    font=('Sans', 8)
                )
                btn.pack(fill='x', padx=10, pady=2)
            self.current_devices = new_devices
        
        self.root.after(5000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

