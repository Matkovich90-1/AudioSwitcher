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
        self.root.geometry("320x350")
        self.root.configure(bg='#1e1e1e')

        
        if platform.system() == "Windows":
            self.root.overrideredirect(True)
            
            self.root.bind("<Button-1>", self.start_move)
            self.root.bind("<B1-Motion>", self.do_move)
        else:
            try: self.root.attributes('-type', 'utility')
            except: pass

        title_bar = tk.Frame(root, bg='#2e2e2e', bd=0)
        title_bar.pack(fill='x')
        
        tk.Label(title_bar, text="  AUDIO OUTPUT", bg='#2e2e2e', fg='gray', 
                 font=('Sans', 7, 'bold')).pack(side='left', pady=2)
        
        tk.Button(title_bar, text="✕", command=root.quit, bg='#2e2e2e', fg='gray', 
                  relief='flat', font=('Sans', 8), padx=10, activebackground='red').pack(side='right')

        self.refresh_btn = tk.Button(root, text="🔄 REFRESH DEVICES", command=self.refresh_ui, 
                                     bg='#333333', fg='#1e88e5', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=10, padx=20, fill='x')

        self.button_frame = tk.Frame(root, bg='#1e1e1e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.active_device_id = None
        self.refresh_ui()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

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
        self.active_device_id = device_id 
        
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        
        self.refresh_ui() 

    def refresh_ui(self):
        self.refresh_btn.config(text="⌛ SCANNING...", state='disabled')
        self.root.update_idletasks()
        
        new_devices = self.get_audio_sinks()
        
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if not new_devices:
            tk.Label(self.button_frame, text="No devices found.", bg='#1e1e1e', fg='gray').pack(pady=20)
        else:
            for dev in new_devices:
                is_active = (dev['id'] == self.active_device_id)
                bg_color = '#1e88e5' if is_active else '#333333'
                fg_color = 'white' if is_active else '#bbbbbb'
                
                btn = tk.Button(self.button_frame, text=f"  {dev['name']}", 
                                command=lambda d=dev['id']: self.switch_audio(d),
                                bg=bg_color, fg=fg_color, relief='flat', anchor='w', padx=10)
                btn.pack(fill='x', padx=15, pady=3)
        
        self.refresh_btn.config(text="🔄 REFRESH DEVICES", state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

