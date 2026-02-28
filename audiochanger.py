import tkinter as tk
import subprocess
import re

class AudioSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Switch")
        self.root.geometry("250x160+50+50") # Slightly wider for long device names
        self.root.attributes('-type', 'utility')
        self.root.configure(bg='#2e2e2e')
        
        self.label = tk.Label(root, text="AUDIO OUTPUT", bg='#2e2e2e', fg='white', font=('Sans', 8, 'bold'))
        self.label.pack(pady=5)

        # Container for the buttons
        self.button_frame = tk.Frame(root, bg='#2e2e2e')
        self.button_frame.pack(fill='both', expand=True)

        self.current_devices = []
        self.refresh_ui()

    def get_audio_sinks(self):
        """Parses wpctl status to find all available sinks."""
        result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
        sinks = []
        
        if "Sinks:" in result.stdout:
            # Extract only the Sinks section
            sinks_section = result.stdout.split("Sinks:")[1].split("Sink endpoints:")[0]
            
            # Regex to find: [id]. [Name] [optional status]
            # Example: 48. Built-in Audio Analog Stereo [vol: 0.40]
            for line in sinks_section.split('\n'):
                match = re.search(r'(\d+)\.\s+(.*)', line)
                if match:
                    node_id = match.group(1)
                    name = match.group(2).strip()
                    is_active = "*" in line
                    
                    # Clean up the name by removing volume/status info at the end
                    clean_name = re.split(r'\[', name)[0].strip()
                    
                    sinks.append({
                        "id": node_id,
                        "name": clean_name,
                        "active": is_active
                    })
        return sinks

    def switch_audio(self, device_id):
        subprocess.run(["wpctl", "set-default", device_id])
        self.refresh_ui()

    def refresh_ui(self):
        new_devices = self.get_audio_sinks()
        
        # Only rebuild buttons if the list of devices or their active status changed
        if new_devices != self.current_devices:
            # Clear existing buttons
            for widget in self.button_frame.winfo_children():
                widget.destroy()

            for dev in new_devices:
                icon = "🔊 " if not dev['active'] else "✅ "
                bg_color = '#1e88e5' if dev['active'] else '#404040'
                
                btn = tk.Button(
                    self.button_frame, 
                    text=f"{icon}{dev['name']}",
                    command=lambda d=dev['id']: self.switch_audio(d),
                    bg=bg_color,
                    fg='white',
                    relief='flat',
                    anchor='w',
                    padx=10
                )
                btn.pack(fill='x', padx=10, pady=2)
            
            self.current_devices = new_devices

        # Check for hardware changes every 2 seconds
        self.root.after(2000, self.refresh_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSwitcher(root)
    root.mainloop()

