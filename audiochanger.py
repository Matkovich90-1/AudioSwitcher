import os
import sys
import platform

# --- FIX: Ensure the sounddevice DLL is found in the bundled EXE ---
if getattr(sys, 'frozen', False) and platform.system() == "Windows":
    # Add the temporary folder (sys._MEIPASS) to the Windows search path
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

import tkinter as tk
import subprocess
import re

# We import sounddevice only after fixing the PATH above
try:
    import sounddevice as sd
except ImportError:
    sd = None

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switch")
        self.root.geometry("320x400")
        self.root.configure(bg='#2e2e2e')
        
        # OS-Specific Window Styling
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 
        else:
            try:
                self.root.attributes('-type', 'utility')
            except:
                pass

        self.label = tk.Label(root, text="SELECT AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 10, 'bold'))
        self.label.pack(pady=15)

        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.refresh_ui()

    def get_audio_sinks(self):
        sinks = []
        try:
            # --- LINUX SIDE (Pop!_OS) ---
            if platform.system() == "Linux":
                result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
                if "Sinks:" in result.stdout:
                    parts = result.stdout.split("Sinks:")
                    sinks_section = parts[1].split("Sink endpoints:")[0]
                    for line in sinks_section.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            node_id = match.group(1)
                            name = re.split(r'\[', match.group(2))[0].strip()
                            sinks.append({"id": node_id, "name": name, "active": "*" in line})
            
            # --- WINDOWS SIDE (sounddevice) ---
            elif platform.system() == "Windows" and sd:
                devices = sd.query_devices()
                unique_names = set()
                for d in devices:
                    # Filter for output devices (speakers/headphones)
                    if d['max_output_channels'] > 0:
                        name = d['name']
                        if name not in unique_names:
                            sinks.append({"id": name, "name": name, "active": False})
                            unique_names.add(name)
        except Exception as e:
            print(f"Error: {e}")
        return sinks

    def switch_audio(self, device_id):
        if platform.system() == "Linux":
            subprocess.run(["wpctl", "set-default", device_id])
        elif platform.system() == "Windows":
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
            nircmd_path = os.path.join(base_path, "nircmd.exe")
            # 0x08000000 = CREATE_NO_WINDOW
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        if len(new_devices) != len(self.current_devices):
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            if not new_devices:
                tk.Label(self.button_frame, text="Scanning for audio hardware...", bg='#2e2e2e', fg='gray').pack(pady=20)
            else:
                for dev in new_devices:
                    icon = "✅ " if dev['active'] else "🔊 "
                    bg_color = '#1e88e5' if dev['active'] else '#404040'
                    btn = tk.Button(
                        self.button_frame, 
                        text=f"{icon}{dev['name']}",
                        command=lambda d=dev['id']: self.switch_audio(d),
                        bg=bg_color, fg='white', relief='flat', anchor='w', padx=10,
                        font=('Sans', 9)
                    )
                    btn.pack(fill='x', padx=15, pady=3)
            self.current_devices = new_devices
        
        # Check every 5 seconds
        self.root.after(5000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
