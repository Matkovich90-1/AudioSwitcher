import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess, re, platform, os, sys, json

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        self.mini_mode = False
        
        # --- POSITION & SIZE (Adjusted for Linux WM padding) ---
        self.main_geo = "320x300+15+15"
        self.mini_geo = "420x95+15+15" 
        self.root.geometry(self.main_geo) 
        self.root.configure(bg='#121212', highlightbackground='#1e88e5', highlightthickness=1)
        
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.environ.get('APPDATA', '.'), 'AudioSwitcher_Config.json')
            import ctypes
            try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: pass
            self.root.overrideredirect(True)
        else:
            self.config_path = os.path.expanduser('~/.audio_switcher_config.json')
            # Using splash type to remove title bar on Linux
            self.root.attributes('-type', 'splash') 
            
        self.config = self.load_config()
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        # --- UI LAYOUT ---
        self.title_bar = tk.Frame(root, bg='#1e1e1e', bd=0)
        self.title_bar.pack(fill='x')
        
        self.ver_label = tk.Label(self.title_bar, text="  AUDIO v1.0.3", bg='#1e1e1e', fg='#666666', font=('Sans', 7, 'bold'))
        self.ver_label.pack(side='left', pady=4)
        
        self.exit_btn = tk.Button(self.title_bar, text="✕", command=root.quit, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8), padx=10, activebackground='#cc3333')
        self.exit_btn.pack(side='right')
        
        self.mini_btn = tk.Button(self.title_bar, text="▢", command=self.toggle_mini, bg='#1e1e1e', fg='#666666', relief='flat', font=('Sans', 8))
        self.mini_btn.pack(side='right', padx=5)

        self.refresh_btn = tk.Button(root, text="REFRESH", command=self.refresh_ui, bg='#121212', fg='#1e88e5', relief='flat', font=('Sans', 8, 'bold'))
        self.refresh_btn.pack(pady=5, padx=15, fill='x')

        self.mini_container = tk.Frame(root, bg='#121212')
        self.main_container = tk.Frame(root, bg='#121212')
        self.main_container.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(self.main_container, bg='#121212', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.button_frame = tk.Frame(self.canvas, bg='#121212')

        self.button_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.button_frame, anchor="nw", width=310)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.refresh_ui()

    def toggle_mini(self):
        self.mini_mode = not self.mini_mode
        if self.mini_mode:
            self.root.geometry(self.mini_geo)
            self.root.attributes("-topmost", True)
            self.refresh_btn.pack_forget()
            self.main_container.pack_forget()
            self.exit_btn.pack_forget()
            self.mini_container.pack(fill='both', expand=True, padx=10, pady=5)
            self.ver_label.config(text="  MINI")
            self.mini_btn.config(text="▲")
        else:
            self.root.geometry(self.main_geo)
            self.root.attributes("-topmost", False)
            self.mini_container.pack_forget()
            self.refresh_btn.pack(pady=5, padx=15, fill='x')
            self.main_container.pack(fill='both', expand=True)
            self.exit_btn.pack(side='right')
            self.ver_label.config(text="  AUDIO v1.0.3")
            self.mini_btn.config(text="▢")
        self.refresh_ui()

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return {"nicknames": data.get("nicknames", {}), "hidden": data.get("hidden", [])}
        except: pass
        return {"nicknames": {}, "hidden": []}

    def get_audio_devices(self, dev_type="Sinks"):
        devices = []
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                stdout = result.stdout
                # Find the 'Audio' section first
                audio_start = stdout.find("Audio")
                if audio_start == -1: return []
                audio_section = stdout[audio_start:]
                # Isolate Sinks or Sources block
                pattern = rf"{dev_type}:(.*?)(?:\n\s*├─|\n\s*└─|\Z)"
                match_section = re.search(pattern, audio_section, re.DOTALL)
                if match_section:
                    for line in match_section.group(1).splitlines():
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            rid = match.group(1)
                            rname = re.split(r'\[', match.group(2))[0].strip()
                            if rname not in self.config["hidden"]:
                                name = self.config["nicknames"].get(rname, rname)
                                devices.append({"id": rid, "name": name, "h_name": rname, "active": "*" in line})
        except: pass
        return devices

    def refresh_ui(self):
        for w in self.button_frame.winfo_children(): w.destroy()
        for w in self.mini_container.winfo_children(): w.destroy()

        sinks = self.get_audio_devices("Sinks")
        sources = self.get_audio_devices("Sources")

        if self.mini_mode:
            # Row 1: Speakers (S)
            s_row = tk.Frame(self.mini_container, bg='#121212')
            s_row.pack(fill='x', pady=1)
            tk.Label(s_row, text="S:", bg='#121212', fg='#1e88e5', font=('Sans', 7, 'bold'), width=2).pack(side='left')
            for dev in sinks:
                bg = '#1e88e5' if dev['active'] else '#1e1e1e'
                tk.Button(s_row, text=dev['name'][:8], command=lambda d=dev['id']: self.switch_audio(d),
                          bg=bg, fg='white', relief='flat', font=('Sans', 7), padx=4).pack(side='left', padx=2)

            # Row 2: Microphones (M)
            m_row = tk.Frame(self.mini_container, bg='#121212')
            m_row.pack(fill='x', pady=1)
            tk.Label(m_row, text="M:", bg='#121212', fg='#1e88e5', font=('Sans', 7, 'bold'), width=2).pack(side='left')
            for dev in sources:
                bg = '#1e88e5' if dev['active'] else '#1e1e1e'
                tk.Button(m_row, text=dev['name'][:8], command=lambda d=dev['id']: self.switch_audio(d),
                          bg=bg, fg='white', relief='flat', font=('Sans', 7), padx=4).pack(side='left', padx=2)
        else:
            tk.Label(self.button_frame, text="SPEAKERS", bg='#121212', fg='#666666', font=('Sans', 7, 'bold')).pack(fill='x', padx=10, pady=(10,2))
            self.create_buttons(sinks)
            tk.Label(self.button_frame, text="MICROPHONES", bg='#121212', fg='#666666', font=('Sans', 7, 'bold')).pack(fill='x', padx=10, pady=(15,2))
            self.create_buttons(sources)

    def create_buttons(self, devices):
        for dev in devices:
            bg = '#1e88e5' if dev['active'] else '#1e1e1e'
            btn = tk.Button(self.button_frame, text=f"  {dev['name']}", 
                            command=lambda d=dev['id']: self.switch_audio(d),
                            bg=bg, fg='white', relief='flat', anchor='w', padx=10, font=('Sans', 9))
            btn.pack(fill='x', padx=10, pady=2)

    def switch_audio(self, device_id):
        # Native wpctl command to set default device
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", str(device_id)])
        self.refresh_ui()

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        x, y = self.root.winfo_x() + (event.x - self.x), self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

