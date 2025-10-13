# 🖱️ Anti-Idle Mouse Mover

A lightweight Python script that keeps your computer “active” during work hours by periodically moving the mouse and pressing a key.  
Useful if you want to prevent your system or messaging apps from showing you as "idle" while you’re working.

---

## 🧩 How It Works

The script uses [`pyautogui`](https://pyautogui.readthedocs.io/en/latest/) to:
- Move the mouse slightly every few seconds
- Press a harmless key (`Ctrl`) to simulate activity
- Automatically stop during your lunch break or at the end of the workday

---

## ⚙️ Usage

### 1. Install dependencies
```bash
pip install pyautogui
