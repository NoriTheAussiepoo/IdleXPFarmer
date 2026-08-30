# Idle XP Farmer

A tiny Windows-friendly Tkinter utility that sends randomized WASD key presses through `pyautogui`.

The app opens a small control panel where you can set a minimum and maximum interval, start the loop, switch to the target window, and watch the next key/countdown status.

## Features

- Randomized interval between key presses
- WASD cycling with visual feedback
- Press counter and elapsed timer
- Start/stop control from a compact Tkinter UI

## Requirements

- Python 3.10 or newer
- `pyautogui`

Tkinter is included with most standard Python installs on Windows.

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Usage

```powershell
python .\afk_wasd_v1.0.pyw
```

Set the interval range, click **START**, then switch focus to the window that should receive the WASD input. Click **STOP** to end the loop.

## Safety Notes

This tool sends real keyboard input to whichever window has focus. Keep the stop button accessible and use it only where automated input is allowed.

`pyautogui.FAILSAFE` is intentionally disabled in this script, so moving the mouse to a screen corner will not stop automation.

You are responsible for how you use this tool. Do not use it with software, games, services, or platforms that prohibit automated input.

## License

This project is licensed under the PolyForm Noncommercial License 1.0.0. See [LICENSE](LICENSE).
