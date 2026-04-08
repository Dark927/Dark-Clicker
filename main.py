import customtkinter as ctk
import pyautogui
import time
from PIL import ImageGrab
from pynput import keyboard, mouse # Added mouse for color picker
from logic import ClickerCore
from sounds import play_success_sound

# Set dark theme globally
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Dual Clicker")
        self.geometry("380x480")
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        self.core = ClickerCore()
        self.p1 = None
        self.p2 = None

        # Hotkey state
        self.stop_hotkey = keyboard.Key.esc
        self.waiting_for_hotkey = False

        # Global hotkey listener
        self.hotkey_listener = keyboard.Listener(on_press=self._on_key_press)
        self.hotkey_listener.start()

        self._build_ui()

    def _on_key_press(self, key):
        # Handle new hotkey assignment
        if self.waiting_for_hotkey:
            self.stop_hotkey = key
            self.waiting_for_hotkey = False
            
            # Format key name for UI
            key_name = str(key).replace('Key.', '').replace("'", "").upper()
            
            # Thread-safe UI updates
            self.after(0, lambda: self.btn_hotkey.configure(text=f"Stop Hotkey: [{key_name}]"))
            self.after(0, lambda: self.lbl_status.configure(text="Hotkey saved!", text_color="gray"))
            play_success_sound()
            return

        # Stop clicker on hotkey press
        if key == self.stop_hotkey:
            if self.core.is_running:
                self.after(0, self.stop)

    def _build_ui(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Auto Clicker Settings", font=("Helvetica", 20, "bold"))
        self.lbl_title.pack(pady=(15, 10))

        # Hotkey Configuration
        self.btn_hotkey = ctk.CTkButton(self, text="Stop Hotkey: [ESC]", fg_color="#444444", hover_color="#555555", command=self.assign_hotkey)
        self.btn_hotkey.pack(pady=(0, 15), padx=20, fill="x")

        # Point 1
        self.btn_p1 = ctk.CTkButton(self, text="1. Set Trigger Button (Hover 3s)", command=lambda: self.grab_point(1))
        self.btn_p1.pack(pady=5, padx=20, fill="x")

        # Point 2
        self.btn_p2 = ctk.CTkButton(self, text="2. Set Action Button (Hover 3s)", command=lambda: self.grab_point(2))
        self.btn_p2.pack(pady=5, padx=20, fill="x")

        # Color Picker Section
        frame_color = ctk.CTkFrame(self, fg_color="transparent")
        frame_color.pack(pady=(15, 5), padx=20, fill="x")
        
        self.btn_color = ctk.CTkButton(frame_color, text="Pick Color (Click)", width=120, command=self.start_color_pick)
        self.btn_color.pack(side="left", padx=(0, 10))
        
        # Color Preview Square
        self.color_preview = ctk.CTkFrame(frame_color, width=25, height=25, fg_color="#FF0000", corner_radius=3)
        self.color_preview.pack(side="left", padx=(0, 10))
        
        self.entry_color = ctk.CTkEntry(frame_color, placeholder_text="#HEX", width=90)
        self.entry_color.insert(0, "#FF0000")
        self.entry_color.pack(side="right", fill="x", expand=True)
        
        # Update preview on manual input
        self.entry_color.bind("<KeyRelease>", self.update_preview_from_entry)

        # Rate Input
        lbl_rate_info = ctk.CTkLabel(self, text="Click Rate Interval:", font=("Helvetica", 12))
        lbl_rate_info.pack(pady=(15, 0), padx=20, anchor="w")

        frame_rate = ctk.CTkFrame(self, fg_color="transparent")
        frame_rate.pack(pady=5, padx=20, fill="x")

        self.entry_rate = ctk.CTkEntry(frame_rate, placeholder_text="e.g., 30")
        self.entry_rate.insert(0, "30")
        self.entry_rate.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_ms = ctk.CTkLabel(frame_rate, text="ms", font=("Helvetica", 14, "bold"))
        self.lbl_ms.pack(side="right")

        # Control Buttons
        self.btn_start = ctk.CTkButton(self, text="START", fg_color="green", hover_color="darkgreen", height=45, command=self.start)
        self.btn_start.pack(pady=(20, 5), padx=20, fill="x")

        self.btn_stop = ctk.CTkButton(self, text="STOP", fg_color="red", hover_color="darkred", state="disabled", height=45, command=self.stop)
        self.btn_stop.pack(pady=5, padx=20, fill="x")

        # Status Line
        self.lbl_status = ctk.CTkLabel(self, text="Status: Ready", text_color="gray")
        self.lbl_status.pack(pady=10)

    def assign_hotkey(self):
        self.waiting_for_hotkey = True
        self.btn_hotkey.configure(text="Press any key to bind...")
        self.lbl_status.configure(text="Waiting for key press...", text_color="orange")

    def grab_point(self, target):
        self.lbl_status.configure(text=f"Move mouse to Point {target}... 3s", text_color="orange")
        self.update()
        time.sleep(3)
        
        x, y = pyautogui.position()
        play_success_sound()
        
        if target == 1:
            self.p1 = (x, y)
            self.btn_p1.configure(text=f"Point 1: {x}, {y}", fg_color="#2b719e")
        else:
            self.p2 = (x, y)
            self.btn_p2.configure(text=f"Point 2: {x}, {y}", fg_color="#2b719e")
            
        self.lbl_status.configure(text="Ready", text_color="gray")

    def start_color_pick(self):
        self.lbl_status.configure(text="Click ANYWHERE to pick color...", text_color="orange")
        self.btn_color.configure(state="disabled") # Prevent double-clicking
        
        # Start one-time listener
        def on_click(x, y, button, pressed):
            if pressed:
                # Get color at cursor
                img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                rgb = img.getpixel((0, 0))[:3]
                hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb).upper()
                
                # Thread-safe UI update
                self.after(0, lambda: self._apply_picked_color(hex_color))
                play_success_sound()
                return False # Stop listener
                
        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def _apply_picked_color(self, hex_color):
        self.entry_color.delete(0, 'end')
        self.entry_color.insert(0, hex_color)
        self.color_preview.configure(fg_color=hex_color)
        self.btn_color.configure(state="normal")
        self.lbl_status.configure(text="Color grabbed!", text_color="gray")

    def update_preview_from_entry(self, event=None):
        # Update preview if valid HEX is typed manually
        hex_val = self.entry_color.get()
        if len(hex_val) == 7 and hex_val.startswith("#"):
            try:
                self.color_preview.configure(fg_color=hex_val)
            except Exception:
                pass

    def start(self):
        if not self.p1 or not self.p2:
            self.lbl_status.configure(text="Error: Set points first!", text_color="red")
            return
            
        try:
            rate = float(self.entry_rate.get())
        except ValueError:
            self.lbl_status.configure(text="Error: Invalid rate!", text_color="red")
            return

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="RUNNING", text_color="green")
        
        color = self.entry_color.get()
        self.core.start_loop(self.p1, self.p2, color, rate)

    def stop(self):
        self.core.stop_loop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        key_name = str(self.stop_hotkey).replace('Key.', '').replace("'", "").upper()
        self.lbl_status.configure(text=f"STOPPED (via {key_name})", text_color="gray")

if __name__ == "__main__":
    app = App()
    app.mainloop()