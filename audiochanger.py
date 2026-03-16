import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess, re, platform, os, sys, json, threading, time

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switcher")
        
        # --- UI CONFIG (300x240 for Windows, 300x160 for Linux) ---
        win_h = 240 if platform.system() == "Windows" else 160
        self.root.geometry(f"300x{win_h}+50+50") 
        self.root.attributes('-alpha', 0.88)
        self.root.configure(bg='#121212', highlightbackground='#1e88e5', highlightthickness=1)
        self.root.overrideredirect(True)

        # --- DATA & CACHE ---
        self.config = self.load_config()
        self.battery_cache = {} # Stores {device_name: "80%"}
        self.active_device_id = None
        self.current_hk = self.config.get("hotkey", "S") # User-settable key

        if platform.system() == "Windows":
            self.config_path = os.path.join(os.environ.get('APPDATA', '.'), 'AudioSwitcher_Config.json')
            import ctypes
            try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: pass
            # BACKGROUND THREADS (Prevents Lag)
            threading.Thread(target=self.setup_windows_hotkey, daemon=True).start()
            threading.Thread(target=self.battery_loop, daemon=True).start()
        else:
            self.config_path = os.path.expanduser('~/.audio_switcher_config.json')
            self.root.attributes('-type', 'dialog') 
            
        # --- UI TOP BAR ---
        title_bar = tk.Frame(root, bg='#1e1e1e', bd=0)
        title_bar.pack(fill='x')
        tk.Label(title_bar, text=f"  AUDIO v1.1.7 [HK: {self.current_hk}]", bg='#1e1e1e', fg='#666666', font=('Consolas', 7, 'bold')).pack(side='left', pady=4)
        tk.Button(title_bar, text="✕", command=root.quit, bg='#1e1e1e', fg='#666666', relief='flat', font=('Consolas', 8), padx=10).pack(side='right')
        tk.Button(title_bar, text="⚙", command=self.unhide_all, bg='#1e1e1e', fg='#666666', relief='flat', font=('Consolas', 8)).pack(side='right', padx=5)

        self.button_frame = tk.Frame(root, bg='#121212')
        self.button_frame.pack(fill='both', expand=True, pady=5)

        self.refresh_ui()
        self.pulse_border()
        
        # Draggable Logic
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

    # --- THE "ZERO-LAG" BATTERY LOOP ---
    def battery_loop(self):
        """Runs once every 5 mins in background. Zero impact on UI speed."""
        while True:
            devices = self.get_audio_sinks()
            for dev in devices:
                try:
                    name = dev['name']
                    ps_cmd = f"Get-PnpDevice -FriendlyName '*{name}*'" + " | Get-PnpDeviceProperty -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' | Select-Object -ExpandProperty Data"
                    res = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, creationflags=0x08000000)
                    val = res.stdout.strip()
                    if val.isdigit():
                        self.battery_cache[name] = f"[{val}%]"
                    else:
                        self.battery_cache[name] = ""
                except: pass
            time.sleep(300) # Wait 5 minutes

    def refresh_ui(self):
        devices = self.get_audio_sinks()
        for w in self.button_frame.winfo_children(): w.destroy()
        
        for dev in devices:
            is_active = dev.get('active') or dev['id'] == self.active_device_id
            bg_c = '#1e88e5' if is_active else '#121212'
            
            # Instant display from cache (No PowerShell wait!)
            batt = self.battery_cache.get(dev['name'], "")
            btn_text = f" › {dev['name'].upper()} {batt}"
            
            btn = tk.Button(self.button_frame, text=btn_text, command=lambda d=dev['id']: self.switch_audio(d),
                            bg=bg_c, fg='white' if is_active else '#aaaaaa', relief='flat', anchor='w', padx=15, 
                            pady=2 if platform.system() == "Linux" else 4, font=('Consolas', 9, 'bold' if is_active else 'normal'), bd=0)
            btn.pack(fill='x', padx=10, pady=1)
            
            if platform.system() == "Windows":
                sc = tk.Scale(self.button_frame, from_=0, to=100, orient='horizontal', bg='#121212', troughcolor='#1e1e1e', 
                              activebackground='#1e88e5', highlightthickness=0, bd=0, showvalue=False, height=3,
                              command=lambda v, d=dev['id']: self.set_volume(d, v))
                # Future logic: slider.set(current_vol)
                sc.pack(fill='x', padx=25, pady=(0, 4))

    # --- RETAIN CORE LOGIC ---
    def switch_audio(self, device_id, silent=True):
        self.active_device_id = device_id
        if platform.system() == "Windows":
            base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd = os.path.join(base, "nircmd.exe")
            subprocess.run([nircmd, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            if not silent: self.show_hud(device_id) # HUD logic here
        else:
            subprocess.run(["wpctl", "set-default", device_id])
        self.refresh_ui()

    def load_config(self):
        # [Existing JSON load logic]
        return {"nicknames": {}, "hidden": [], "hotkey": "S"}

    def setup_windows_hotkey(self):
        # [Existing ctypes RegisterHotKey logic]
        pass

    def start_move(self, event): self.x, self.y = event.x, event.y
    def do_move(self, event):
        x, y = self.root.winfo_x()+(event.x-self.x), self.root.winfo_y()+(event.y-self.y)
        self.root.geometry(f"+{x}+{y}")

    def pulse_border(self, phase=0):
        # [Existing pulse logic]
        pass
    
    def get_audio_sinks(self):
        # [Existing wpctl/powershell logic]
        return []

    def unhide_all(self):
        self.config["hidden"] = []; self.refresh_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
