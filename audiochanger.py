import tkinter as tk
import subprocess
import re
import platform
import os
import sys

# Windows-only flag to hide console windows
CREATE_NO_WINDOW = 0x08000000

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.root.geometry("300x280")
        self.root.configure(bg='#2e2e2e')
        
        # OS-Specific Window Styling
        if platform.system() == "Linux":
            try:
                self.root.attributes('-type', 'utility')
            except:
                pass 
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
                # Original Linux logic
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
                # STEALTH: Added creationflags to hide PowerShell window
                proc = subprocess.run(
                    ["powershell", "-Command", "Get-CimInstance Win32_SoundDevice | Select-Object Name"], 
                    capture_output=True, 
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )
                # Skip PowerShell headers (first 3 lines)
                lines = proc.stdout.splitlines()
                if len(lines) > 3:
                    for line in lines[3:]:
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
            # Find bundled nircmd.exe
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            
            # STEALTH: Added creationflags to hide NirCmd execution
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=CREATE_NO_WINDOW)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=CREATE_NO_WINDOW)
        
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
        # Refresh every 3 seconds to detect plug/unplug events
        self.root.after(3000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

