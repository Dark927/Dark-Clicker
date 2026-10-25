import customtkinter as ctk
import pyautogui
import time
import ctypes
import tkinter as tk
from PIL import ImageGrab
from pynput import keyboard, mouse
from logic import ClickerCore
from sounds import play_success_sound

# Ensure High-DPI awareness on Windows before creating any Tkinter windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class SnippingOverlay:
    """
    Transparent fullscreen overlay that allows the user to click & drag
    to select a rectangular region on screen.
    """
    def __init__(self, parent, on_selection_complete):
        self.parent = parent
        self.on_selection_complete = on_selection_complete
        
        self.overlay = tk.Toplevel(parent)
        self.overlay.attributes('-alpha', 0.28)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        self.overlay.config(cursor='cross')
        self.overlay.overrideredirect(True)

        self.canvas = tk.Canvas(self.overlay, cursor='cross', bg='grey15', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.text_id = None

        # Bindings
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.overlay.bind('<Escape>', lambda e: self.cancel())

        # Hint text
        w = self.overlay.winfo_screenwidth()
        self.canvas.create_text(
            w // 2, 60,
            text="Drag mouse to select Area for Point 2 | Press ESC to cancel",
            fill="white",
            font=("Segoe UI", 16, "bold")
        )

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#38BDF8", width=2, fill="#0284C7"
        )
        self.text_id = self.canvas.create_text(
            self.start_x, max(20, self.start_y - 15),
            text="0 x 0", fill="#FFFFFF", font=("Segoe UI", 11, "bold"), anchor="w"
        )

    def on_drag(self, event):
        cur_x, cur_y = event.x, event.y
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
            width = abs(cur_x - self.start_x)
            height = abs(cur_y - self.start_y)
            top_y = min(self.start_y, cur_y)
            left_x = min(self.start_x, cur_x)
            self.canvas.coords(self.text_id, left_x, max(20, top_y - 12))
            self.canvas.itemconfig(self.text_id, text=f"{width} x {height} px")

    def on_release(self, event):
        end_x, end_y = event.x, event.y
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self.overlay.destroy()

        # If selection has meaningful size (> 5x5 px)
        if (x2 - x1) >= 5 and (y2 - y1) >= 5:
            self.on_selection_complete((x1, y1, x2, y2))
        else:
            # Treated as single click
            self.on_selection_complete((end_x, end_y))

    def cancel(self):
        self.overlay.destroy()


class ModernClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Configuration
        self.title("Smart Dual Clicker Pro")
        self.geometry("450x750")
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        # Theme initial state
        self.current_theme = "dark"
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")
        
        self.core = ClickerCore()
        self.p1 = None
        self.p2 = None  # (x, y) or (x1, y1, x2, y2)

        # Hotkey state
        self.stop_hotkey = keyboard.Key.esc
        self.waiting_for_hotkey = False

        # Global hotkey listener
        self.hotkey_listener = keyboard.Listener(on_press=self._on_key_press)
        self.hotkey_listener.start()

        self._build_ui()

    def toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_btn.configure(text="🌙 Dark Mode")
        else:
            self.current_theme = "dark"
            self.theme_btn.configure(text="☀️ Light Mode")
        ctk.set_appearance_mode(self.current_theme)

    def _on_key_press(self, key):
        if self.waiting_for_hotkey:
            self.stop_hotkey = key
            self.waiting_for_hotkey = False
            key_name = str(key).replace('Key.', '').replace("'", "").upper()
            self.after(0, lambda: self.btn_hotkey.configure(text=f"Panic Stop: [{key_name}]"))
            self.after(0, lambda: self.lbl_status.configure(text="Hotkey saved!", text_color="#10b981"))
            play_success_sound()
            return

        if key == self.stop_hotkey:
            if self.core.is_running:
                self.after(0, self.stop)

    def _build_ui(self):
        # Outer Card with glassmorphic styling
        self.main_card = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=("#F1F5F9", "#171923"),
            border_width=1,
            border_color=("#CBD5E1", "#2D3748")
        )
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        # Header bar
        header_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="⚡ Smart Clicker",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        title_lbl.pack(side="left")

        self.theme_btn = ctk.CTkButton(
            header_frame,
            text="☀️ Light Mode",
            width=100,
            height=28,
            corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#E2E8F0", "#2D3748"),
            hover_color=("#CBD5E1", "#4A5568"),
            text_color=("#1A202C", "#F7FAFC"),
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right")

        # Emergency Hotkey Pill Button
        self.btn_hotkey = ctk.CTkButton(
            self.main_card,
            text="Panic Stop: [ESC]",
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#475569", "#2D3748"),
            hover_color=("#64748B", "#4A5568"),
            command=self.assign_hotkey
        )
        self.btn_hotkey.pack(fill="x", padx=16, pady=(4, 8))

        # --- Section 1: Coordinates Card ---
        coord_card = ctk.CTkFrame(
            self.main_card,
            corner_radius=14,
            fg_color=("#FFFFFF", "#1E2230"),
            border_width=1,
            border_color=("#E2E8F0", "#2D3748")
        )
        coord_card.pack(fill="x", padx=16, pady=4)

        self.btn_p1 = ctk.CTkButton(
            coord_card,
            text="🎯 Set Point 1 (Trigger - Hover 3s)",
            height=34,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#2563EB", "#3B82F6"),
            hover_color=("#1D4ED8", "#2563EB"),
            command=lambda: self.grab_point(1)
        )
        self.btn_p1.pack(fill="x", padx=12, pady=(10, 6))

        # Point 2 Selection row with 2 options: Single Point OR Select Area
        f_p2_buttons = ctk.CTkFrame(coord_card, fg_color="transparent")
        f_p2_buttons.pack(fill="x", padx=12, pady=(0, 6))

        self.btn_p2 = ctk.CTkButton(
            f_p2_buttons,
            text="🎯 Set Point 2",
            height=34,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#2563EB", "#3B82F6"),
            hover_color=("#1D4ED8", "#2563EB"),
            command=lambda: self.grab_point(2)
        )
        self.btn_p2.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_p2_area = ctk.CTkButton(
            f_p2_buttons,
            text="📐 Select Area",
            height=34,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#0D9488", "#14B8A6"),
            hover_color=("#0F766E", "#0D9488"),
            command=self.start_area_selection
        )
        self.btn_p2_area.pack(side="right", fill="x", expand=True)

        self.chk_double_click = ctk.CTkCheckBox(
            coord_card,
            text="⚡ Double-click on Point 2",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=6,
            checkbox_width=20,
            checkbox_height=20
        )
        self.chk_double_click.select()
        self.chk_double_click.pack(anchor="w", padx=14, pady=(2, 10))

        # --- Section 2: Colors Eyedroppers Card ---
        color_card = ctk.CTkFrame(
            self.main_card,
            corner_radius=14,
            fg_color=("#FFFFFF", "#1E2230"),
            border_width=1,
            border_color=("#E2E8F0", "#2D3748")
        )
        color_card.pack(fill="x", padx=16, pady=6)

        # Eyedropper 1
        f_c1 = ctk.CTkFrame(color_card, fg_color="transparent")
        f_c1.pack(fill="x", padx=12, pady=(10, 6))

        self.btn_color1 = ctk.CTkButton(
            f_c1,
            text="💧 Pick Color 1",
            width=115,
            height=32,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#DB2777", "#EC4899"),
            hover_color=("#BE185D", "#DB2777"),
            command=lambda: self.start_color_pick(1)
        )
        self.btn_color1.pack(side="left")

        self.color_preview1 = ctk.CTkFrame(f_c1, width=28, height=28, fg_color="#FFB6C1", corner_radius=8)
        self.color_preview1.pack(side="left", padx=10)

        self.entry_color1 = ctk.CTkEntry(
            f_c1,
            height=32,
            corner_radius=10,
            placeholder_text="#FFB6C1",
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.entry_color1.insert(0, "#FFB6C1")
        self.entry_color1.pack(side="right", fill="x", expand=True)
        self.entry_color1.bind("<KeyRelease>", lambda e: self.update_preview_from_entry(1))

        # Eyedropper 2
        f_c2 = ctk.CTkFrame(color_card, fg_color="transparent")
        f_c2.pack(fill="x", padx=12, pady=(0, 10))

        self.chk_color2 = ctk.CTkCheckBox(
            f_c2,
            text="",
            width=20,
            corner_radius=6,
            checkbox_width=20,
            checkbox_height=20,
            command=self.toggle_color2
        )
        self.chk_color2.select()
        self.chk_color2.pack(side="left", padx=(0, 4))

        self.btn_color2 = ctk.CTkButton(
            f_c2,
            text="💧 Pick Color 2",
            width=115,
            height=32,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#0284C7", "#0EA5E9"),
            hover_color=("#0369A1", "#0284C7"),
            command=lambda: self.start_color_pick(2)
        )
        self.btn_color2.pack(side="left")

        self.color_preview2 = ctk.CTkFrame(f_c2, width=28, height=28, fg_color="#A5C8EE", corner_radius=8)
        self.color_preview2.pack(side="left", padx=10)

        self.entry_color2 = ctk.CTkEntry(
            f_c2,
            height=32,
            corner_radius=10,
            placeholder_text="#A5C8EE",
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.entry_color2.insert(0, "#A5C8EE")
        self.entry_color2.pack(side="right", fill="x", expand=True)
        self.entry_color2.bind("<KeyRelease>", lambda e: self.update_preview_from_entry(2))

        # --- Section 3: Batch Limits & Rate Control ---
        config_frame = ctk.CTkFrame(
            self.main_card,
            corner_radius=14,
            fg_color=("#FFFFFF", "#1E2230"),
            border_width=1,
            border_color=("#E2E8F0", "#2D3748")
        )
        config_frame.pack(fill="x", padx=16, pady=4)

        # Batch limit row
        f_batch_inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        f_batch_inner.pack(fill="x", padx=12, pady=(8, 4))

        lbl_batch = ctk.CTkLabel(
            f_batch_inner,
            text="🎯 Max Orders / Batch:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        lbl_batch.pack(side="left")

        lbl_batch_hint = ctk.CTkLabel(
            f_batch_inner,
            text="(0 = All nearest)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#9CA3AF"
        )
        lbl_batch_hint.pack(side="left", padx=(4, 0))

        self.entry_batch = ctk.CTkEntry(
            f_batch_inner,
            width=70,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.entry_batch.insert(0, "0")
        self.entry_batch.pack(side="right")

        # Interval Rate row
        f_rate_inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        f_rate_inner.pack(fill="x", padx=12, pady=(4, 8))

        lbl_rate = ctk.CTkLabel(
            f_rate_inner,
            text="⏱️ Interval Rate:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        lbl_rate.pack(side="left")

        self.lbl_ms = ctk.CTkLabel(
            f_rate_inner,
            text="ms",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.lbl_ms.pack(side="right", padx=(6, 0))

        self.entry_rate = ctk.CTkEntry(
            f_rate_inner,
            width=70,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.entry_rate.insert(0, "0")
        self.entry_rate.pack(side="right")

        # --- Section 4: Action Buttons (START / STOP) ---
        actions_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        actions_frame.pack(fill="x", padx=16, pady=(10, 4))

        self.btn_start = ctk.CTkButton(
            actions_frame,
            text="▶ START",
            height=46,
            corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self.start
        )
        self.btn_start.pack(fill="x", pady=(0, 6))

        self.btn_stop = ctk.CTkButton(
            actions_frame,
            text="⏹ STOP",
            height=42,
            corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            state="disabled",
            command=self.stop
        )
        self.btn_stop.pack(fill="x")

        # --- Status pill ---
        self.lbl_status = ctk.CTkLabel(
            self.main_card,
            text="Status: Ready",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#9CA3AF"
        )
        self.lbl_status.pack(pady=(6, 8))

    def toggle_color2(self):
        state = "normal" if self.chk_color2.get() else "disabled"
        self.btn_color2.configure(state=state)
        self.entry_color2.configure(state=state)

    def assign_hotkey(self):
        self.waiting_for_hotkey = True
        self.btn_hotkey.configure(text="Press any key to bind...")
        self.lbl_status.configure(text="Waiting for key press...", text_color="#F59E0B")

    def grab_point(self, target):
        self.lbl_status.configure(text=f"Hover over Point {target}... (3s countdown)", text_color="#F59E0B")
        self.update()
        time.sleep(3)
        
        x, y = pyautogui.position()
        play_success_sound()
        
        if target == 1:
            self.p1 = (x, y)
            self.btn_p1.configure(text=f"Point 1: {x}, {y}", fg_color="#10B981")
        else:
            self.p2 = (x, y)
            self.btn_p2.configure(text=f"Point 2: {x}, {y}", fg_color="#10B981")
            self.btn_p2_area.configure(text="📐 Select Area", fg_color=("#0D9488", "#14B8A6"))
            
        self.lbl_status.configure(text="Point captured!", text_color="#10B981")

    def start_area_selection(self):
        self.lbl_status.configure(text="Drag cursor on screen to select Area for Point 2...", text_color="#F59E0B")
        SnippingOverlay(self, self._on_area_selected)

    def _on_area_selected(self, coords):
        play_success_sound()
        if len(coords) == 4:
            x1, y1, x2, y2 = coords
            self.p2 = (x1, y1, x2, y2)
            w = x2 - x1
            h = y2 - y1
            self.btn_p2_area.configure(text=f"Area: {w}x{h} px", fg_color="#10B981")
            self.btn_p2.configure(text="Point 2: [Area Selected]", fg_color="#10B981")
            self.lbl_status.configure(text=f"Point 2 Area set: ({x1},{y1}) to ({x2},{y2}) [{w}x{h}]", text_color="#10B981")
        else:
            x, y = coords
            self.p2 = (x, y)
            self.btn_p2.configure(text=f"Point 2: {x}, {y}", fg_color="#10B981")
            self.btn_p2_area.configure(text="📐 Select Area", fg_color=("#0D9488", "#14B8A6"))
            self.lbl_status.configure(text=f"Point 2 set: {x}, {y}", text_color="#10B981")

    def start_color_pick(self, target_num=1):
        target_name = f"Color {target_num}"
        self.lbl_status.configure(text=f"Click ANYWHERE to sample {target_name}...", text_color="#F59E0B")
        btn = self.btn_color1 if target_num == 1 else self.btn_color2
        btn.configure(state="disabled")
        
        def on_click(x, y, button, pressed):
            if pressed:
                img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                rgb = img.getpixel((0, 0))[:3]
                hex_color = '#{:02X}{:02X}{:02X}'.format(*rgb)
                
                self.after(0, lambda: self._apply_picked_color(hex_color, target_num))
                play_success_sound()
                return False
                
        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def _apply_picked_color(self, hex_color, target_num=1):
        if target_num == 1:
            self.entry_color1.delete(0, 'end')
            self.entry_color1.insert(0, hex_color)
            self.color_preview1.configure(fg_color=hex_color)
            self.btn_color1.configure(state="normal")
        else:
            self.entry_color2.delete(0, 'end')
            self.entry_color2.insert(0, hex_color)
            self.color_preview2.configure(fg_color=hex_color)
            self.btn_color2.configure(state="normal")
            
        self.lbl_status.configure(text=f"Color {target_num} grabbed successfully!", text_color="#10B981")

    def update_preview_from_entry(self, target_num=1):
        entry = self.entry_color1 if target_num == 1 else self.entry_color2
        preview = self.color_preview1 if target_num == 1 else self.color_preview2
        hex_val = entry.get().strip()
        if len(hex_val) == 7 and hex_val.startswith("#"):
            try:
                preview.configure(fg_color=hex_val)
            except Exception:
                pass

    def start(self):
        if not self.p1 or not self.p2:
            self.lbl_status.configure(text="Error: Set both points/areas first!", text_color="#EF4444")
            return
            
        try:
            rate = float(self.entry_rate.get())
        except ValueError:
            self.lbl_status.configure(text="Error: Invalid rate number!", text_color="#EF4444")
            return

        try:
            batch_limit = int(self.entry_batch.get())
        except ValueError:
            batch_limit = 0

        color1 = self.entry_color1.get().strip()
        color2 = self.entry_color2.get().strip()
        use_color2 = bool(self.chk_color2.get())
        double_click = bool(self.chk_double_click.get())

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="● RUNNING", text_color="#10B981")
        
        self.core.start_loop(
            p1=self.p1,
            p2=self.p2,
            hex_color1=color1,
            hex_color2=color2,
            use_color2=use_color2,
            double_click=double_click,
            max_batch_orders=batch_limit,
            rate=rate,
            tolerance=20
        )

    def stop(self):
        self.core.stop_loop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        key_name = str(self.stop_hotkey).replace('Key.', '').replace("'", "").upper()
        self.lbl_status.configure(text=f"STOPPED (via {key_name})", text_color="#9CA3AF")

if __name__ == "__main__":
    app = ModernClickerApp()
    app.mainloop()
