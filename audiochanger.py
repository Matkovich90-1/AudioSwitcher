import tkinter as tk
import subprocess
import platform
import os
import sys
import re
import sounddevice as sd

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switch")
        self.root.geometry("320x350")
        self.root.configure(bg='#2e2e2e')
        
        if platform.system() == "Windows":
            self.root.attributes('-toolwindow', True)
            self.root.attributes('-topmost', True) 
        else:
            try: self.root.attributes('-type', 'utility')
            except: pass

        tk.Label(root, text="AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 10, 'bold')).pack(pady=10)
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
                    s_section = result.stdout.split("Sinks:")[1].split("Sink endpoints:")[0]
                    for line in s_section.split('\n'):
                        match = re.search(r'(\d+)\.\s+(.*)', line)
                        if match:
                            sinks.append({"id": match.group(1), "name": match.group(2).split("[")[0].strip(), "active": "*" in line})
            
            elif platform.system() == "Windows":
                # Modern, fast, and silent way to get devices
                devices = sd.query_devices()
                unique_names = set()
                for d in devices:
                    # max_output_channels > 0 means it is a speaker/headphone
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
            # Force switch (1=Default, 2=Communication)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "1"], creationflags=0x08000000)
            subprocess.run([nircmd_path, "setdefaultsounddevice", device_id, "2"], creationflags=0x08000000)
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        if len(new_devices) != len(self.current_devices):
            for widget in self.button_frame.winfo_children(): widget.destroy()
            for dev in new_devices:
                bg_color = '#1e88e5' if dev['active'] else '#404040'
                btn = tk.Button(self.button_frame, text=f"🔊 {dev['name']}", 
                                command=lambda d=dev['id']: self.switch_audio(d),
                                bg=bg_color, fg='white', relief='flat', anchor='w', padx=10)
                btn.pack(fill='x', padx=15, pady=3)
            self.current_devices = new_devices
        self.root.after(5000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()
