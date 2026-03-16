import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess, re, platform, os, sys, json

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        
        # --- POSITION, SIZE & TRANSPARENCY ---
        self.root.geometry("300x200+15+15") 
        self.root.attributes('-alpha', 0.88)
        self.root.configure(bg='#121212', highlightbackground='#1e88e5', highlightthickness=1)
        
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.environ.get('APPDATA', '.'), 'AudioSwitcher_Config.json')
            import ctypes
            try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: pass
            self.root.overrideredirect(True)
        else:
            self.config_path = os.path.expanduser('~/.audio_switcher_config.json')
            self.root.attributes('-type', 'dialog') 
            
        self.config = self.load_config()
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.active_menu = None
        self.active_device_id = None

        # --- UI TOP BAR ---
        title_bar = tk.Frame(root, bg='#1e1e1e', bd=0)
        title_bar.pack(fill='x')
        tk.Label(title_bar, text="  AUDIO v1.0.4", bg='#1e1e1e', fg='#666666', 
                 font=('Consolas', 8, 'bold')).pack(side='left', pady=4)
        
        # Title bar buttons - removed borders for Linux sleekness
        tk.Button(title_bar, text="✕", command=root.quit, bg='#1e1e1e', fg='#666666', 
                  relief='flat', font=('Consolas', 9), padx=10, activebackground='#cc3333',
                  bd=0, highlightthickness=0).pack(side='right')
        
        tk.Button(title_bar, text="⚙", command=self.unhide_all, bg='#1e1e1e', fg='#666666', 
                  relief='flat', font=('Consolas', 9), bd=0, highlightthickness=0).pack(side='right', padx=5)

        self.refresh_btn = tk.Button(root, text="SCAN HARDWARE", command=self.refresh_ui, 
                                    bg='#121212', fg='#1e88e5', relief='flat', 
                                    font=('Consolas', 8, 'bold'), activebackground='#121212', 
                                    activeforeground='#ffffff', bd=1, highlightthickness=0)
        self.refresh_btn.pack(pady=10, padx=15, fill='x')

        self.button_frame = tk.Frame(root, bg='#121212')
        self.button_frame.pack(fill='both', expand=True)

        self.refresh_ui()
        self.pulse_border()

    def pulse_border(self, phase=0):
        colors = ["#1e88e5", "#1565c0", "#0d47a1", "#1565c0"]
        self.root.configure(highlightbackground=colors[phase])
        self.root.after(1000, lambda: self.pulse_border((phase + 1) % len(colors)))

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

    def get_audio_sinks(self):
        sinks = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    lines = result.stdout.split('\n')
                    is_sink_section = False
                    for line in lines:
                        if "Sinks:" in line: is_sink_section = True
                        if is_sink_section and "Sink endpoints:" in line: break
                        if is_sink_section:
                            match = re.search(r'(\d+)\.\s+(.*?)(?:\s+\[|$)', line)
                            if match:
                                raw_id, raw_name = match.group(1), match.group(2).strip()
                                if raw_name not in self.config["hidden"]:
                                    name = self.config["nicknames"].get(raw_name, raw_name)
                                    sinks.append({"id": raw_id, "name": name, "h_name": raw_name, "active": "*" in line})
            
            elif platform.system() == "Windows":
                # For Windows, we'll keep the powershell discovery for now
                cmd = 'powershell -Command "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name"'
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
                for line in proc.stdout.splitlines():
                    name = line.strip()
                    if name and name not in self.config["hidden"]:
                        display_name = self.config["nicknames"].get(name, name)
                        sinks.append({"id": name, "name": display_name, "h_name": name, "active": False})
        except: pass
        return sinks

    def refresh_ui(self):
        devices = self.get_audio_sinks()
        for widget in self.button_frame.winfo_children(): widget.destroy()
        
        for dev in devices:
            is_active = dev.get('active', False) or (dev['id'] == self.active_device_id)
            base_bg = '#1e88e5' if is_active else '#121212'
            hover_bg = '#2196f3' if is_active else '#1c1c1c'
            fg_color = 'white' if is_active else '#aaaaaa'
            
            # THE SLEEK FIX: Added bd=0 and highlightthickness=0 to kill the white outlines
            btn = tk.Button(self.button_frame, text=f" › {dev['name'].upper()}", 
                            command=lambda d=dev['id']: self.switch_audio(d),
                            bg=base_bg, fg=fg_color, relief='flat', anchor='w', 
                            padx=15, pady=5, font=('Consolas', 9, 'bold' if is_active else 'normal'),
                            bd=0, highlightthickness=0)
            btn.pack(fill='x', padx=10, pady=2)
            
            btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.configure(bg=h, fg='white'))
            btn.bind("<Leave>", lambda e, b=btn, o=base_bg, f=fg_color: b.configure(bg=o, fg=f))
            btn.bind("<Button-3>", lambda e, n=dev['h_name']: self.show_menu(e, n))

    def switch_audio(self, device_id):
        self.active_device_id = device_id
        try:
            if platform.system() == "Linux":
                subprocess.run(["wpctl", "set-default", device_id])
            elif platform.system() == "Windows":
                base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
                nircmd = os.path.join(base_path, "nircmd.exe")
                # Using 1 for console and 2 for multimedia sets both
                subprocess.run([nircmd, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
                subprocess.run([nircmd, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        except: pass
        self.refresh_ui()

    def start_move(self, event):
        if self.active_menu: self.active_menu.destroy()
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def rename_device(self, hardware_name):
        new_name = simpledialog.askstring("Nickname", "New Name:", parent=self.root)
        if new_name:
            self.config["nicknames"][hardware_name] = new_name
            self.save_config(); self.refresh_ui()

    def hide_device(self, hardware_name):
        self.config["hidden"].append(hardware_name)
        self.save_config(); self.refresh_ui()

    def unhide_all(self):
        self.config["hidden"] = []
        self.save_config(); self.refresh_ui()
        messagebox.showinfo("Reset", "All devices visible.")

    def show_menu(self, event, hardware_name):
        if self.active_menu: self.active_menu.destroy()
        self.active_menu = tk.Menu(self.root, tearoff=0, bg='#1e1e1e', fg='white', 
                                   activebackground='#1e88e5', font=('Consolas', 9), bd=0)
        self.active_menu.add_command(label="Rename", command=lambda: self.rename_device(hardware_name))
        self.active_menu.add_command(label="Hide", command=lambda: self.hide_device(hardware_name))
        self.active_menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

