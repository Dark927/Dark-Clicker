import platform
import os

def play_success_sound():
    # Play native system sound without extra libraries
    system = platform.system()
    if system == "Windows":
        import winsound
        winsound.MessageBeep(winsound.MB_OK)
    elif system == "Darwin":  # macOS
        os.system("afplay /System/Library/Sounds/Glass.aiff &")
    else:
        print('\a')