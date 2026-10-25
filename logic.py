import threading
import time
import ctypes
import pyautogui
import numpy as np
from PIL import ImageGrab

# Ensure process is DPI aware so screen coordinates map 1:1 on all displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Disable PyAutoGUI artificial delays completely
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False

# Win32 direct mouse input API for zero-overhead clicking
user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

def win32_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def win32_double_click(x, y, interval=0.04):
    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    if interval > 0:
        time.sleep(interval)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class ClickerCore:
    def __init__(self):
        self.is_running = False
        self.pos1 = None
        self.pos2 = None  # (x, y) or (x1, y1, x2, y2)
        self.target_hex1 = "#FFB6C1"
        self.target_hex2 = "#A5C8EE"
        self.use_color2 = True
        self.double_click = True
        self.max_batch_orders = 0  # 0 = unlimited / all
        self.tolerance = 20
        self.rate_ms = 0

    def hex_to_rgb(self, hex_color):
        if not hex_color:
            return None
        hex_color = hex_color.strip().lstrip('#')
        if len(hex_color) != 6:
            return None
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    def color_matches(self, current_rgb, target_rgb, tolerance=20):
        if not target_rgb or not current_rgb:
            return False
        return (abs(current_rgb[0] - target_rgb[0]) <= tolerance and
                abs(current_rgb[1] - target_rgb[1]) <= tolerance and
                abs(current_rgb[2] - target_rgb[2]) <= tolerance)

    def get_pixel_color(self, x, y):
        try:
            img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
            return img.getpixel((0, 0))[:3]
        except Exception:
            return None

    def find_all_matching_targets_in_area(self, area, target_rgb1, target_rgb2, tolerance=20):
        """
        Segment-based row detection across area = (x1, y1, x2, y2).
        Extracts each distinct table row containing Color 1 or Color 2.
        Returns a list of screen coordinates: [(click_x, click_y), ...]
        """
        x1, y1, x2, y2 = area
        if x2 <= x1 or y2 <= y1:
            return []
        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            arr = np.array(img)[:, :, :3]
        except Exception:
            return []

        H, W, _ = arr.shape
        arr_int = arr.astype(np.int16)

        mask = np.zeros((H, W), dtype=bool)

        if target_rgb1:
            t1 = np.array(target_rgb1, dtype=np.int16)
            diff1 = np.abs(arr_int - t1)
            mask |= np.all(diff1 <= tolerance, axis=2)

        if target_rgb2:
            t2 = np.array(target_rgb2, dtype=np.int16)
            diff2 = np.abs(arr_int - t2)
            mask |= np.all(diff2 <= tolerance, axis=2)

        # Count matching pixels on each horizontal line y
        row_counts = np.sum(mask, axis=1)

        # A valid row line must have at least 15 matching pixels
        has_color = row_counts > 15

        # Find contiguous vertical segments representing rows
        segments = []
        start = None
        for y in range(H):
            if has_color[y]:
                if start is None:
                    start = y
            else:
                if start is not None:
                    if (y - start) >= 6:  # Minimum row thickness 6px
                        segments.append((start, y - 1))
                    start = None
        if start is not None and (H - start) >= 6:
            segments.append((start, H - 1))

        # Split unusually tall segments if multiple rows are contiguous without borders
        final_segments = []
        for (s, e) in segments:
            h = e - s + 1
            if h > 42:
                num_rows = round(h / 25.0)
                if num_rows > 1:
                    step = h / num_rows
                    for j in range(num_rows):
                        sub_s = int(s + j * step)
                        sub_e = int(s + (j + 1) * step - 1)
                        final_segments.append((sub_s, sub_e))
                    continue
            final_segments.append((s, e))

        # Calculate exact click coordinates (center of each detected row)
        targets = []
        for (s, e) in final_segments:
            mid_y = (s + e) // 2
            xs = np.where(mask[mid_y, :])[0]
            if len(xs) == 0:
                xs = np.where(np.any(mask[s:e+1, :], axis=0))[0]
            click_x = int(np.median(xs)) if len(xs) > 0 else W // 2
            targets.append((x1 + click_x, y1 + mid_y))

        return targets

    def start_loop(self, p1, p2, hex_color1, hex_color2=None, use_color2=True, double_click=True, max_batch_orders=0, rate=0, tolerance=20):
        self.pos1 = p1
        self.pos2 = p2
        self.target_hex1 = hex_color1
        self.target_hex2 = hex_color2
        self.use_color2 = use_color2
        self.double_click = double_click
        self.max_batch_orders = max(0, int(max_batch_orders))
        self.rate_ms = rate
        self.tolerance = tolerance
        self.is_running = True
        
        # Start high-speed background thread
        threading.Thread(target=self._loop, daemon=True).start()

    def stop_loop(self):
        self.is_running = False

    def _loop(self):
        target_rgb1 = self.hex_to_rgb(self.target_hex1)
        target_rgb2 = self.hex_to_rgb(self.target_hex2) if self.use_color2 else None
        
        is_area = len(self.pos2) == 4
        p1_x, p1_y = self.pos1[0], self.pos1[1]

        while self.is_running:
            # 1. Trigger / Refresh click at Point 1
            win32_click(p1_x, p1_y)
            
            # Pause to allow the application / browser / 1C to reload and render orders
            time.sleep(0.08)
            
            # 2. Evaluate Point 2
            if is_area:
                targets = self.find_all_matching_targets_in_area(
                    self.pos2, target_rgb1, target_rgb2, self.tolerance
                )
                
                if targets:
                    # Sort targets strictly by Euclidean distance from Point 1 (nearest first)
                    targets.sort(key=lambda pt: (pt[0] - p1_x) ** 2 + (pt[1] - p1_y) ** 2)
                    
                    # Batching logic:
                    # If max_batch_orders == 0: click ALL available matching orders in area
                    # If max_batch_orders > 0: click at most N nearest orders (or all available if < N)
                    if self.max_batch_orders > 0:
                        orders_to_click = targets[:self.max_batch_orders]
                    else:
                        orders_to_click = targets
                    
                    # Click on each designated order in this batch
                    for (cx, cy) in orders_to_click:
                        if not self.is_running:
                            break
                            
                        if self.double_click:
                            win32_double_click(cx, cy, interval=0.04)
                        else:
                            win32_click(cx, cy)
                            if target_rgb2:
                                time.sleep(0.04)
                                c = self.get_pixel_color(cx, cy)
                                if c and self.color_matches(c, target_rgb2, self.tolerance):
                                    win32_click(cx, cy)
                        
                        # Small delay after clicking each order so that:
                        # 1) The order state cleanly registers and updates in UI
                        # 2) The clicker distinctly processes 1 to N orders without counting the same row multiple times
                        time.sleep(0.12)
            else:
                # Single point mode
                current_color = self.get_pixel_color(self.pos2[0], self.pos2[1])
                if current_color:
                    matched_c1 = bool(target_rgb1 and self.color_matches(current_color, target_rgb1, self.tolerance))
                    matched_c2 = bool(target_rgb2 and self.color_matches(current_color, target_rgb2, self.tolerance))
                    
                    if matched_c1 or matched_c2:
                        if self.double_click:
                            win32_double_click(self.pos2[0], self.pos2[1], interval=0.04)
                        else:
                            win32_click(self.pos2[0], self.pos2[1])
                            if matched_c1 and target_rgb2:
                                time.sleep(0.04)
                                new_c = self.get_pixel_color(self.pos2[0], self.pos2[1])
                                if new_c and self.color_matches(new_c, target_rgb2, self.tolerance):
                                    win32_click(self.pos2[0], self.pos2[1])
                        time.sleep(0.12)

            # 3. Only sleep if user specified interval > 0 before starting the next batch cycle
            if self.rate_ms > 0:
                time.sleep(self.rate_ms / 1000.0)
