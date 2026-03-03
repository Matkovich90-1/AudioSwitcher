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
        self.root.geometry("320x320")
        self.root.configure(bg='#2e2e2e')
        
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
 
        else:
            try: self.root.attributes('-type', 'utility')
            except: pass

        # --- REFRESH BUTTON (This is the fix) ---
        tk.Label(root, text="AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 10, 'bold')).pack(pady=10)
        
        self.refresh_btn = tk.Button(root, text="🔄 REFRESH DEVICES", command=self.refresh_ui, 
                                     bg='#1e88e5', fg='white', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=5, padx=20, fill='x')

        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.refresh_ui()

    def get_audio_sinks(self):
        sinks = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    parts = result.stdout.split("Sinks:")
                    s_section = parts[1].split("Sink endpoints:")[0]
                    for line in s_section.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            sinks.append({"id": match.group(1), "name": match.group(2).split("[")[0].strip()})
            
            elif platform.system() == "Windows":
                # Using the most compatible PowerShell command for Win11
                cmd = 'powershell -Command "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name"'
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
                for line in proc.stdout.splitlines():
                    name = line.strip()
                    if name:
                        sinks.append({"id": name, "name": name})
        except Exception as e:
            print(f"Error: {e}")
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            # 0x08000000 = CREATE_NO_WINDOW
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        
        # Show a temporary status message
        status = tk.Label(self.root, text=f"Switched!", bg='#2e2e2e', fg='#4CAF50')
        status.pack()
        self.root.after(2000, status.destroy)

    def refresh_ui(self):
        # Disable button while scanning
        self.refresh_btn.config(text="⌛ SCANNING...", state='disabled')
        self.root.update_idletasks()
        
        new_devices = self.get_audio_sinks()
        
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if not new_devices:
            tk.Label(self.button_frame, text="No devices found.\nCheck connections & Refresh.", bg='#2e2e2e', fg='gray').pack(pady=20)
        else:
            for dev in new_devices:
                btn = tk.Button(self.button_frame, text=f"🔊 {dev['name']}", 
                                command=lambda d=dev['id']: self.switch_audio(d),
                                bg='#404040', fg='white', relief='flat', anchor='w', padx=10)
                btn.pack(fill='x', padx=15, pady=3)
        
        self.refresh_btn.config(text="🔄 REFRESH DEVICES", state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

