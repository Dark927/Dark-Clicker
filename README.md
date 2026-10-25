# Smart Dual Clicker

<img width="485" height="649" alt="{A19506CB-A283-4AFA-8AAC-271FA55DA19B}" src="https://github.com/user-attachments/assets/d8c9edd1-11dd-42a0-a535-edd96704dab5" />


## Overview
Smart Dual Clicker is a lightweight, cross-platform automation tool built with Python and CustomTkinter. It performs automated clicking across two distinct screen coordinates with a conditional logic flow: the second coordinate is clicked only if a specified target color is detected at that exact pixel location.

## Features
* **Conditional Logic:** Executes a primary trigger click, evaluates the pixel color at Point 2, and executes a secondary click/double-click when matching either target color.
* **Random Delay Window for Point 2:** Configurable randomized delay window (`[Min, Max]` in ms) before clicking on Point 2 (supports both Single Point and Area Selection modes). After Point 1 triggers and matching target colors are confirmed, it waits a random duration within the window before clicking Point 2.
* **Auto-Stop on Color 2 Disappearance & Retry:** When Color 2 is enabled, configure a wait time and enable auto-stop. After clicking Color 2, it waits the designated time. If Color 2 disappears from the clicked point, the clicker automatically halts and announces completion. If Color 2 is still present on the same point, it clicks again and continues waiting until processed.
* **Batch Limit & Nearest-to-Point-1 Prioritization:** Configure `Max Orders / Batch` (e.g. `1`, `3`, `5`, or `0` for unlimited). When multiple matching orders appear in the area, the clicker calculates the Euclidean distance to Point 1 and prioritizes clicking the **$N$ closest orders** first.
* **Point 2 Area Selection:** Choose between targeting an exact coordinate or clicking **"📐 Select Area"** to drag-select an entire screen zone (e.g. table rows or list area). When a color match is detected anywhere inside the area, it clicks the exact matched coordinate.
* **Double-Click Option:** Supports automated double-clicking on Point 2 (configurable with a checkbox, enabled by default) for applications like 1C:Enterprise where opening an item requires a double-click.
* **Dual Eyedroppers:** Two independent eyedroppers allowing you to match multiple colors (e.g., Color 1 for pink unselected row, and Color 2 for blue selected row).
* **Color Tolerance:** Performs color matching within a tolerance threshold to handle UI focus gradients and anti-aliasing variations smoothly.
* **Coordinate Mapping:** Set target points simply by hovering the cursor over the desired location for 3 seconds.
* **Integrated Color Pickers:** Click anywhere on the screen to capture exact HEX color codes for Color 1 and Color 2.
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
4. **Double-Click Setting:** Toggle the "Double-click on Point 2" checkbox as needed (checked by default).
5. **Target Colors (Dual Eyedroppers):**
   * **Color 1:** Click "Pick Color 1" and click on the screen to sample the primary target color (e.g. pink `#FFB6C1`).
   * **Color 2:** Enable the checkbox for Color 2, click "Pick Color 2", and sample the selected row color (e.g. blue `#A5C8EE`).
   * **Stop on Color 2 Disappear:** Enable "Stop on Color 2 disappear" and enter the wait delay in ms. When active, it clicks Color 2, waits the delay, checks if Color 2 disappeared from the clicked location (stopping if so), and re-clicks if still present.
6. **Timing & Limits:**
   * **Max Orders / Batch:** Number of nearest matching orders to process per cycle (0 = all).
   * **Interval Rate:** Milliseconds to wait before repeating the batch cycle.
   * **Random Delay P2:** Checkbox with `[Min - Max]` ms range to wait randomly before clicking Point 2 once valid colors are detected.
7. **Execution:** Press "START". To halt the script, press "STOP" or use your designated global hotkey.

## Testing
A local test bench is provided in [`test_page.html`](file:///f:/Computer-Science/Dark-Clicker/test_page.html):
1. Double-click `test_page.html` to open it in your browser.
2. It replicates the 1C order table with:
   - **Trigger Button (Point 1):** Increments trigger count.
   - **Order Row (Point 2):** Starts pink (`#FFB6C1`), switches to blue (`#A5C8EE`) on single click, and marks as "Done" on double-click.
3. Test your clicker against this page without needing 1C open.

## Building for Windows
To package the app into a single `.exe` file:
- Run `build.bat` or run:
  ```bash
  python -m PyInstaller --onefile --noconsole --name "Dark-Clicker" main.py
  ```
- The output executable will be placed in `dist/Dark-Clicker.exe`.

## OS-Specific Requirements

### macOS
For the application to function correctly on macOS, you must grant the terminal (or the compiled `.app`) the following permissions in `System Settings > Privacy & Security`:
* **Accessibility:** Required for `pyautogui` and `pynput` to simulate mouse clicks and listen for the global hotkey.
* **Screen Recording:** Required for `Pillow` (ImageGrab) to read pixel colors.

### Windows
If the script is compiled into an `.exe` using PyInstaller, Windows Defender or other antivirus software may flag the executable as a false positive due to the nature of mouse automation and global keyboard listeners. You may need to add the executable to your antivirus whitelist.
