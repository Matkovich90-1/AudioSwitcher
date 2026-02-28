import tkinter as tk
import subprocess
import re
import platform
import os
import sys

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x250")
        self.root.configure(bg='#2e2e2e')
        
        # FIX: OS-Specific Window Styling
        if platform.system() == "Linux":
            try:
                # Styles the window as a small utility popup on Pop!_OS
                self.root.attributes('-type', 'utility')
            except:
                pass 
        elif platform.system() == "Windows":
            # Styles it as a tool window (no minimize/maximize) on Windows 11
            self.root.attributes('-toolwindow', True)
            # Keeps it on top of other windows so you can find it easily
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
                # Linux/Pipewire Logic
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    parts = result.stdout.split("Sinks:")
                    if len(parts) > 1:
                        sinks_section = parts[1].split("Sink endpoints:")[0]
                        for line in sinks_section.split('\n'):
                            match = re.search(r'(\d+)\.\s+(.*)', line)
                            if match:
                                sinks.append({
                                    "id": match.group(1),
                                    "name": re.split(r'\[', match.group(2))[0].strip(),
                                    "active": "*" in line
                                })
            
            elif platform.system() == "Windows":
                # Windows Logic: Using PowerShell to list playback devices
                proc = subprocess.run(["powershell", "-Command", "Get-CimInstance Win32_SoundDevice | Select-Object Name"], capture_output=True, text=True)
                for line in proc.stdout.splitlines()[3:]: # Skip PowerShell headers
                    name = line.strip()
                    if name:
                        sinks.append({"id": name, "name": name, "active": False})
        except Exception as e:
            print(f"Error fetching devices: {e}")
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            # Path handling for the bundled nircmd.exe
            if getattr(sys, 'frozen', False):
                # If running as .exe, find nircmd inside the temporary folder
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            
            # Use NirCmd to force switch default output (bypasses Windows lock)
            # 1 = Default Multimedia, 2 = Default Communications
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"])
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"])
        
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        if new_devices != self.current_devices:
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            for dev in new_devices:
                icon = "✅ " if dev['active'] else "🔊 "
                bg_color = '#1e88e5' if dev['active'] else '#404040'
                
                btn = tk.Button(
                    self.button_frame, 
                    text=f"{icon}{dev['name']}",
                    command=lambda d=dev['id']: self.switch_audio(d),
                    bg=bg_color, fg='white', relief='flat', anchor='w', padx=10
                )
                btn.pack(fill='x', padx=10, pady=2)
            self.current_devices = new_devices
        # Checks for hardware changes every 3 seconds
        self.root.after(3000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
