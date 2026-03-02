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
        self.root.geometry("320x400")
        self.root.configure(bg='#2e2e2e')
        
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 
        else:
            try: self.root.attributes('-type', 'utility')
            except: pass

        # --- HEADER & REFRESH BUTTON ---
        tk.Label(root, text="AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 10, 'bold')).pack(pady=10)
        
        self.refresh_btn = tk.Button(root, text="🔄 REFRESH DEVICES", command=self.refresh_ui, 
                                     bg='#1e88e5', fg='white', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=5, padx=20, fill='x')

        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.refresh_ui()

    def get_audio_sinks(self):
        sinks = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    parts = result.stdout.split("Sinks:")[1].split("Sink endpoints:")[0]
                    for line in parts.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            sinks.append({"id": match.group(1), "name": match.group(2).split("[")[0].strip()})
            
            elif platform.system() == "Windows":
                # STEALTH POWERSHELL: Runs only when you click 'Refresh'
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
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            # Force switch (1=Default, 2=Communication)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        # Note: We don't auto-refresh here to save resources
        self.label_status = tk.Label(self.root, text=f"Switched to {device_id[:15]}...", bg='#2e2e2e', fg='#4CAF50', font=('Sans', 7))
        self.label_status.pack()
        self.root.after(2000, self.label_status.destroy)

    def refresh_ui(self):
        # Change button text to show it's working
        self.refresh_btn.config(text="⌛ SCANNING...", state='disabled')
        self.root.update_idletasks()
        
        new_devices = self.get_audio_sinks()
        
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if not new_devices:
            tk.Label(self.button_frame, text="No devices found.\nClick Refresh.", bg='#2e2e2e', fg='gray').pack(pady=20)
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

