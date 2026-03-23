import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess, re, platform, os, sys, json

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        
        self.root.geometry("320x300+15+15") 
        self.root.update_idletasks()
        self.root.minsize(320, 300)
        self.root.configure(bg='#121212', highlightbackground='#1e88e5', highlightthickness=1)
        
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.environ.get('APPDATA', '.'), 'AudioSwitcher_Config.json')
            import ctypes
            try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: pass
            self.root.overrideredirect(True)
        else:
            self.config_path = os.path.expanduser('~/.audio_switcher_config.json')
            self.root.attributes('-type', 'splash') 
            
        self.config = self.load_config()
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.active_menu = None
        self.active_sink_id = None
        self.active_source_id = None

        # Title Bar
        title_bar = tk.Frame(root, bg='#1e1e1e', bd=0)
        title_bar.pack(fill='x')
        tk.Label(title_bar, text="  AUDIO v1.1.0", bg='#1e1e1e', fg='#666666', font=('Sans', 7, 'bold')).pack(side='left', pady=4)
        
        tk.Button(title_bar, text="⚙", command=self.unhide_all, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8)).pack(side='right', padx=5)
        tk.Button(title_bar, text="✕", command=root.quit, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8), padx=10, activebackground='#cc3333').pack(side='right')

        # Refresh Button
        self.refresh_btn = tk.Button(root, text="REFRESH DEVICES", command=self.refresh_ui, bg='#121212', fg='#1e88e5', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=5, padx=15, fill='x')

        # Scrollable Container for Devices
        self.container = tk.Frame(root, bg='#121212')
        self.container.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(self.container, bg='#121212', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.button_frame = tk.Frame(self.canvas, bg='#121212')

        self.button_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.button_frame, anchor="nw", width=310)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.refresh_ui()

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return {"nicknames": data.get("nicknames", {}), "hidden": data.get("hidden", [])}
        except: pass
        return {"nicknames": {}, "hidden": []}

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except: pass

    def rename_device(self, hardware_name):
        new_name = simpledialog.askstring("Nickname", "Rename Device:", parent=self.root)
        if new_name is not None:
            self.config["nicknames"][hardware_name] = new_name
            self.save_config()
            self.refresh_ui()

    def hide_device(self, hardware_name):
        if hardware_name not in self.config["hidden"]:
            self.config["hidden"].append(hardware_name)
            self.save_config()
            self.refresh_ui()

    def unhide_all(self):
        self.config["hidden"] = []
        self.save_config()
        self.refresh_ui()
        messagebox.showinfo("Settings", "All devices restored!", parent=self.root)

    def show_menu(self, event, hardware_name):
        if self.active_menu: self.active_menu.destroy()
        self.active_menu = tk.Menu(self.root, tearoff=0, bg='#1e1e1e', fg='white', activebackground='#1e88e5')
        self.active_menu.add_command(label="Rename", command=lambda: self.rename_device(hardware_name))
        self.active_menu.add_command(label="Hide", command=lambda: self.hide_device(hardware_name))
        self.active_menu.post(event.x_root, event.y_root)

    def get_audio_devices(self, dev_type="Sinks"):
        devices = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                stdout = result.stdout
                
                # Isolate the Audio section
                audio_start = stdout.find("Audio")
                if audio_start == -1: return []
                audio_section = stdout[audio_start:]
                
                # Extract only the Sinks or Sources block using a regex that stops at the next branch
                pattern = rf"{dev_type}:(.*?)(?:\n\s*├─|\n\s*└─|\Z)"
                match_section = re.search(pattern, audio_section, re.DOTALL)
                
                if match_section:
                    lines = match_section.group(1).splitlines()
                    for line in lines:
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            raw_id = match.group(1)
                            raw_name = re.split(r'\[', match.group(2))[0].strip()
                            if raw_name not in self.config["hidden"]:
                                name = self.config["nicknames"].get(raw_name, raw_name)
                                devices.append({"id": raw_id, "name": name, "h_name": raw_name, "active": "*" in line})
            
            elif platform.system() == "Windows":
                # Basic Windows logic using PowerShell
                wmi_class = "Win32_SoundDevice" if dev_type == "Sinks" else "Win32_PnPEntity WHERE Category='AudioEndpoint'"
                cmd = f'powershell -Command "Get-CimInstance {wmi_class} | Select-Object -ExpandProperty Name"'
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
                for line in proc.stdout.splitlines():
                    name = line.strip()
                    if name and name not in self.config["hidden"]:
                        display_name = self.config["nicknames"].get(name, name)
                        devices.append({"id": name, "name": display_name, "h_name": name, "active": False})
        except: pass
        return devices

    def refresh_ui(self):
        for widget in self.button_frame.winfo_children(): widget.destroy()
        
        # Speakers Section
        tk.Label(self.button_frame, text="SPEAKERS", bg='#121212', fg='#666666', font=('Sans', 7, 'bold')).pack(fill='x', padx=10, pady=(10,2))
        self.create_buttons(self.get_audio_devices("Sinks"), is_mic=False)
        
        # Microphones Section
        tk.Label(self.button_frame, text="MICROPHONES", bg='#121212', fg='#666666', font=('Sans', 7, 'bold')).pack(fill='x', padx=10, pady=(15,2))
        self.create_buttons(self.get_audio_devices("Sources"), is_mic=True)

    def create_buttons(self, devices, is_mic):
        for dev in devices:
            current_active = self.active_source_id if is_mic else self.active_sink_id
            is_active = dev.get('active', False) or (dev['id'] == current_active)
            
            bg_color = '#1e88e5' if is_active else '#1e1e1e'
            btn = tk.Button(self.button_frame, text=f"  {dev['name']}", 
                            command=lambda d=dev['id'], m=is_mic: self.switch_audio(d, m),
                            bg=bg_color, fg='white', relief='flat', anchor='w', padx=10, font=('Sans', 9))
            btn.pack(fill='x', padx=10, pady=2)
            btn.bind("<Button-3>", lambda e, n=dev['h_name']: self.show_menu(e, n))

    def switch_audio(self, device_id, is_mic):
        if is_mic: self.active_source_id = device_id
        else: self.active_sink_id = device_id
        
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            
        self.refresh_ui()

    def start_move(self, event):
        if self.active_menu: self.active_menu.destroy()
        self.x = event.x; self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

