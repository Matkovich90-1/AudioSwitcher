import tk as tk
from tkinter import simpledialog, messagebox
import subprocess, re, platform, os, sys, json

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        
        self.mini_mode = False
        self.active_menu = None
        self.active_device_id = None
        
        # --- INITIAL CONFIG & POSITION ---
        self.root.geometry("300x200+15+15") 
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

        # UI ELEMENTS
        self.title_bar = tk.Frame(root, bg='#1e1e1e', bd=0)
        self.title_bar.pack(fill='x')
        tk.Label(self.title_bar, text="  AUDIO v1.0.2", bg='#1e1e1e', fg='#666666', font=('Sans', 7, 'bold')).pack(side='left', pady=4)
        
        tk.Button(self.title_bar, text="✕", command=root.quit, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8), padx=10, activebackground='#cc3333').pack(side='right')
        self.mini_btn = tk.Button(self.title_bar, text="⬜", command=self.toggle_mini, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8))
        self.mini_btn.pack(side='right', padx=5)
        tk.Button(self.title_bar, text="⚙", command=self.unhide_all, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8)).pack(side='right', padx=5)

        self.refresh_btn = tk.Button(root, text="REFRESH DEVICES", command=self.refresh_ui, bg='#121212', fg='#1e88e5', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=5, padx=15, fill='x')

        self.button_frame = tk.Frame(root, bg='#121212')
        self.button_frame.pack(fill='both', expand=True)

        self.set_window_constraints(300, 200)
        self.refresh_ui()

    def set_window_constraints(self, w, h):
        self.root.minsize(0, 0)
        self.root.maxsize(3000, 3000)
        self.root.geometry(f"{w}x{h}")
        self.root.update_idletasks()
        self.root.minsize(w, h)
        self.root.maxsize(w, h)

    def toggle_mini(self):
        self.mini_mode = not self.mini_mode
        if self.mini_mode:
            self.root.attributes('-topmost', True)
            self.refresh_btn.pack_forget()
            self.title_bar.pack_forget()
            devices = self.get_audio_sinks()
            new_width = max(150, (len(devices) * 105) + 45)
            self.set_window_constraints(new_width, 45)
        else:
            self.root.attributes('-topmost', False)
            self.title_bar.pack(fill='x', before=self.button_frame)
            self.refresh_btn.pack(pady=5, padx=15, fill='x', after=self.title_bar)
            self.set_window_constraints(300, 200)
        self.refresh_ui()

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
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
                    s_section = result.stdout.split("Sinks:")[1].split("Sink endpoints:")[0]
                    for line in s_section.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            raw_id = match.group(1)
                            raw_name = match.group(2).split('[')[0].strip()
                            if raw_name not in self.config.get("hidden", []):
                                name = self.config.get("nicknames", {}).get(raw_name, raw_name)
                                sinks.append({"id": raw_id, "name": name, "h_name": raw_name, "active": "*" in line})
            elif platform.system() == "Windows":
                cmd = 'powershell -Command "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name"'
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
                for line in proc.stdout.splitlines():
                    name = line.strip()
                    if name and name not in self.config.get("hidden", []):
                        display_name = self.config.get("nicknames", {}).get(name, name)
                        sinks.append({"id": name, "name": display_name, "h_name": name, "active": False})
        except: pass
        return sinks

    def refresh_ui(self):
        devices = self.get_audio_sinks()
        for widget in self.button_frame.winfo_children(): widget.destroy()
        
        if self.mini_mode:
            tk.Button(self.button_frame, text="🔙", command=self.toggle_mini, 
                      bg='#1e1e1e', fg='#1e88e5', relief='flat', font=('Sans', 10), width=3).pack(side='left', padx=(5,2), pady=5)

        for dev in devices:
            # FIX: Bind the ID immediately to the lambda to avoid 'Late Binding' bug
            d_id = dev['id']
            h_name = dev['h_name']
            is_active = dev.get('active', False) or (d_id == self.active_device_id)
            bg_color = '#1e88e5' if is_active else '#1e1e1e'
            
            if self.mini_mode:
                btn = tk.Button(self.button_frame, text=dev['name'][:12], 
                                command=lambda id_val=d_id: self.switch_audio(id_val),
                                bg=bg_color, fg='white', relief='flat', font=('Sans', 8), width=12)
                btn.pack(side='left', padx=2, pady=5)
            else:
                btn = tk.Button(self.button_frame, text=f"  {dev['name']}", 
                                command=lambda id_val=d_id: self.switch_audio(id_val),
                                bg=bg_color if is_active else '#121212', fg='white', relief='flat', 
                                anchor='w', padx=10, font=('Sans', 9))
                btn.pack(fill='x', padx=10, pady=2)
            
            btn.bind("<Button-3>", lambda e, n=h_name: self.show_menu(e, n))

    def switch_audio(self, device_id):
        self.active_device_id = device_id
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            if os.path.exists(nircmd_path):
                subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
                subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        self.refresh_ui()

    def start_move(self, event):
        if self.active_menu: self.active_menu.destroy()
        self.x = event.x; self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def rename_device(self, hardware_name):
        new_name = simpledialog.askstring("Nickname", f"Rename Device:", parent=self.root)
        if new_name:
            self.config["nicknames"][hardware_name] = new_name
            self.save_config(); self.refresh_ui()

    def hide_device(self, hardware_name):
        if hardware_name not in self.config["hidden"]:
            self.config["hidden"].append(hardware_name)
            self.save_config(); self.refresh_ui()

    def unhide_all(self):
        self.config["hidden"] = []
        self.save_config(); self.refresh_ui()
        messagebox.showinfo("Settings", "All devices restored!", parent=self.root)

    def show_menu(self, event, hardware_name):
        if self.active_menu: self.active_menu.destroy()
        self.active_menu = tk.Menu(self.root, tearoff=0, bg='#1e1e1e', fg='white', activebackground='#1e88e5')
        self.active_menu.add_command(label="Rename", command=lambda: self.rename_device(hardware_name))
        self.active_menu.add_command(label="Hide", command=lambda: self.hide_device(hardware_name))
        self.active_menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
