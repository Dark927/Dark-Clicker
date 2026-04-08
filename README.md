# Smart Dual Clicker

<img width="485" height="649" alt="{A19506CB-A283-4AFA-8AAC-271FA55DA19B}" src="https://github.com/user-attachments/assets/d8c9edd1-11dd-42a0-a535-edd96704dab5" />


## Overview
Smart Dual Clicker is a lightweight, cross-platform automation tool built with Python and CustomTkinter. It performs automated clicking across two distinct screen coordinates with a conditional logic flow: the second coordinate is only clicked if a specified target color is detected at that exact pixel location.

## Features
* **Conditional Logic:** Executes a primary click, evaluates the pixel color at a secondary location, and executes a secondary click only upon a color match.
* **Coordinate Mapping:** Set target points simply by hovering the cursor over the desired location for 3 seconds.
* **Integrated Color Picker:** Click anywhere on the screen to capture the exact HEX color code for the condition.
* **Global Hotkey:** Includes a global emergency stop key (default: ESC) that functions even when the application is running in the background. The hotkey can be dynamically reassigned within the interface.
* **Modern UI:** Built with CustomTkinter for a responsive, dark-themed graphical interface.

## Prerequisites
Ensure Python 3.8 or higher is installed. The following external libraries are required:

```bash
pip install customtkinter pyautogui Pillow pynput
```

## Usage
1. Run the application via terminal or command prompt: `python main.py`
2. **Set Point 1 (Trigger):** Click the corresponding button, move your cursor to the desired location, and wait 3 seconds. A system sound will confirm the coordinates are saved.
3. **Set Point 2 (Action):** Repeat the process for the second point.
4. **Target Color:** Click "Pick Color (Click)" and click anywhere on your screen to sample the required color. The HEX value and a color preview will update automatically.
5. **Rate:** Enter the desired interval between click cycles in milliseconds (e.g., 30 for 0.03 seconds).
6. **Execution:** Press "START". To halt the script, press "STOP" or use your designated global hotkey.

## OS-Specific Requirements

### macOS
For the application to function correctly on macOS, you must grant the terminal (or the compiled `.app`) the following permissions in `System Settings > Privacy & Security`:
* **Accessibility:** Required for `pyautogui` and `pynput` to simulate mouse clicks and listen for the global hotkey.
* **Screen Recording:** Required for `Pillow` (ImageGrab) to read pixel colors.

### Windows
If the script is compiled into an `.exe` using PyInstaller, Windows Defender or other antivirus software may flag the executable as a false positive due to the nature of mouse automation and global keyboard listeners. You may need to add the executable to your antivirus whitelist.
