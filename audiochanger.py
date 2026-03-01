import tkinter as tk
import subprocess
import platform
import os
import sys
import ctypes

# Windows-only Stealth Flags
CREATE_NO_WINDOW = 0x08000000
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0

def get_startup_info():
    """Creates a startupinfo object that forces windows to stay hidden."""
    if platform.system() == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= STARTF_USESHOWWINDOW
        si.wShowWindow = SW_HIDE
        return si
    return None

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x280")
        self.root.configure(bg='#2e2e2e')
        
        if platform.system() == "Linux":
            try: self.root.attributes('-type', 'utility')
            except: pass 
        elif platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 

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
                if "Sinks:" in result.stdout:
                    s_section = result.stdout.split("Sinks:")[1].split("Sink endpoints:")[0]
                    for line in s_section.split('\n'):
                        if "." in line:
                            parts = line.strip().split(".")
                            sinks.append({"id": parts[0], "name": parts[1].split("[")[0].strip(), "active": "*" in line})
            
            elif platform.system() == "Windows":
                # NEW: Direct WMIC call (faster than PowerShell and easier to hide)
                cmd = 'wmic path Win32_SoundDevice get Name'
                proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, startupinfo=get_startup_info())
                for line in proc.stdout.splitlines()[1:]:
                    name = line.strip()
                    if name: sinks.append({"id": name, "name": name, "active": False})
        except Exception as e:
            print(f"Error: {e}")
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            
            # Use stealth flags for the switch commands
            si = get_startup_info()
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=CREATE_NO_WINDOW, startupinfo=si)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=CREATE_NO_WINDOW, startupinfo=si)
        
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        if new_devices != self.current_devices:
            for widget in self.button_frame.winfo_children(): widget.destroy()
            for dev in new_devices:
                bg_color = '#1e88e5' if dev['active'] else '#404040'
                btn = tk.Button(self.button_frame, text=f"🔊 {dev['name']}", command=lambda d=dev['id']: self.switch_audio(d),
                                bg=bg_color, fg='white', relief='flat', anchor='w', padx=10)
                btn.pack(fill='x', padx=10, pady=2)
            self.current_devices = new_devices
        self.root.after(5000, self.refresh_ui) # Slowed to 5s to reduce system load

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
