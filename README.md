# Stay Awake

Small Python utilities to keep your workstation active while you are present and working.

This repository currently includes:
- `mover.py`: lightweight timed mouse movement + key press script for work hours
- `clicker.py`: configurable auto-clicker with a desktop UI (and terminal fallback)

## What These Scripts Do

Both tools use `pyautogui` to simulate light activity:
- Move/click the mouse
- Press `Ctrl` periodically
- Support safe interruption (`Ctrl+C` and PyAutoGUI failsafe)

## Important Safety Notes

- PyAutoGUI failsafe is enabled. Moving the mouse to the top-left corner can stop actions.
- Use responsibly and only where this behavior is allowed by your workplace policies.
- Test with harmless targets first before running unattended loops.

## Requirements

- Windows (current workspace target)
- Python version from `pyproject.toml` (`>=3.14`)
- Dependencies:
	- `pyautogui`
	- `pynput`
	- `numpy`

## Installation

### Option 1: Using `uv` (recommended)

```powershell
uv sync
```

### Option 2: Using `pip`

```powershell
pip install pyautogui pynput numpy
```

## Run

### Mouse mover

```powershell
uv run python mover.py
```

Behavior summary:
- Runs in a loop with activity checks every few seconds
- Keeps activity during morning or afternoon windows
- Stops at lunch transition (from morning to 13:00) or at end of day (18:00+)

### Auto clicker (GUI)

```powershell
uv run python clicker.py
```

GUI features:
- Choose click interval
- Choose button (`left`, `right`, `middle`)
- Optional double-click mode
- Optional return-to-original-mouse-position mode
- Finite click count or infinite mode (`0`)
- Click target capture from your next real click

Terminal fallback:
- If Tkinter UI is unavailable, the script automatically switches to CLI prompts.

## Stop / Exit

- `mover.py`: press `Ctrl+C` in terminal
- `clicker.py`:
	- Press the app `Stop` button, or
	- Press `Ctrl+C` in terminal mode, or
	- Trigger PyAutoGUI failsafe by moving cursor to top-left corner

## Troubleshooting

- `Missing dependency: pynput`
	- Install dependencies again (`uv sync` or `pip install pynput`)
- GUI does not open
	- Tkinter may be unavailable; script should fall back to terminal mode
- Script seems to do nothing
	- Ensure screen/session is active and mouse/keyboard permissions are not blocked by system settings

## Project Files

- `mover.py`: activity mover loop with time-window stop conditions
- `clicker.py`: Tkinter auto-clicker + CLI fallback
- `pyproject.toml`: project metadata and dependencies
- `command_line.txt`: quick launch command example
