import threading
import time
import pyautogui
from PIL import ImageGrab

class ClickerCore:
    def __init__(self):
        self.is_running = False
        self.pos1 = None
        self.pos2 = None
        self.target_hex = "#FFFFFF"
        self.rate_ms = 30

    def hex_to_rgb(self, hex_color):
        # Convert #FF0000 to (255, 0, 0)
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_pixel_color(self, x, y):
        # Grab exactly 1 pixel for maximum performance
        img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
        # Handle RGBA (Mac sometimes returns 4 channels)
        return img.getpixel((0, 0))[:3] 

    def start_loop(self, p1, p2, hex_color, rate):
        self.pos1 = p1
        self.pos2 = p2
        self.target_hex = hex_color
        self.rate_ms = rate
        self.is_running = True
        
        # Start background thread
        threading.Thread(target=self._loop, daemon=True).start()

    def stop_loop(self):
        self.is_running = False

    def _loop(self):
        target_rgb = self.hex_to_rgb(self.target_hex)
        rate_sec = self.rate_ms / 1000.0
        
        while self.is_running:
            # First unconditional click
            pyautogui.click(x=self.pos1[0], y=self.pos1[1])
            
            # Second conditional click
            current_color = self.get_pixel_color(self.pos2[0], self.pos2[1])
            if current_color == target_rgb:
                pyautogui.click(x=self.pos2[0], y=self.pos2[1])
                
            time.sleep(rate_sec)