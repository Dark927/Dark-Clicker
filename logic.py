import threading
import time
import pyautogui
from PIL import ImageGrab

class ClickerCore:
    def __init__(self):
        self.is_running = False
        self.pos1 = None
        self.pos2 = None
        self.target_hex1 = "#FFB6C1"
        self.target_hex2 = "#A5C8EE"
        self.use_color2 = True
        self.double_click = True
        self.tolerance = 20
        self.rate_ms = 30

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
        # Grab exactly 1 pixel for maximum performance
        img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
        # Handle RGBA (Mac/Windows sometimes returns 4 channels)
        return img.getpixel((0, 0))[:3]

    def _execute_click_at_point2(self):
        if self.double_click:
            pyautogui.doubleClick(x=self.pos2[0], y=self.pos2[1], interval=0.05)
        else:
            pyautogui.click(x=self.pos2[0], y=self.pos2[1])

    def start_loop(self, p1, p2, hex_color1, hex_color2=None, use_color2=True, double_click=True, rate=30, tolerance=20):
        self.pos1 = p1
        self.pos2 = p2
        self.target_hex1 = hex_color1
        self.target_hex2 = hex_color2
        self.use_color2 = use_color2
        self.double_click = double_click
        self.rate_ms = rate
        self.tolerance = tolerance
        self.is_running = True
        
        # Start background thread
        threading.Thread(target=self._loop, daemon=True).start()

    def stop_loop(self):
        self.is_running = False

    def _loop(self):
        target_rgb1 = self.hex_to_rgb(self.target_hex1)
        target_rgb2 = self.hex_to_rgb(self.target_hex2) if self.use_color2 else None
        rate_sec = max(0.001, self.rate_ms / 1000.0)
        
        while self.is_running:
            # 1. First trigger click at Point 1
            pyautogui.click(x=self.pos1[0], y=self.pos1[1])
            
            # 2. Check pixel color at Point 2
            current_color = self.get_pixel_color(self.pos2[0], self.pos2[1])
            
            # Check for match with Color 1 or Color 2
            matched_color1 = bool(target_rgb1 and self.color_matches(current_color, target_rgb1, self.tolerance))
            matched_color2 = bool(target_rgb2 and self.color_matches(current_color, target_rgb2, self.tolerance))
            
            if matched_color1 or matched_color2:
                # Perform click on Point 2
                self._execute_click_at_point2()
                
                # If double_click was disabled and Color 1 was matched (e.g. pink),
                # the click may have selected the row and immediately turned it into Color 2 (blue).
                # If Color 2 is enabled, detect the transition and immediately execute the second click!
                if not self.double_click and matched_color1 and target_rgb2:
                    time.sleep(0.05)
                    new_color = self.get_pixel_color(self.pos2[0], self.pos2[1])
                    if self.color_matches(new_color, target_rgb2, self.tolerance):
                        self._execute_click_at_point2()
                
            time.sleep(rate_sec)
