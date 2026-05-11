import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

try:
    from pynput import mouse
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: pynput\nInstall with: pip install pynput"
    ) from exc


class MouseClickerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Mouse Clicker")
        self.root.geometry("430x290")
        self.root.resizable(False, False)

        # Runtime state
        self.running = False
        self.waiting_for_target = False
        self.target_pos: tuple[int, int] | None = None
        self.click_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self.interval_var = tk.StringVar(value="1.0")
        self.button_var = tk.StringVar(value="left")
        self.double_click_var = tk.BooleanVar(value=False)
        self.click_count_var = tk.StringVar(value="0")  # 0 means infinite
        self.status_var = tk.StringVar(value="Set parameters and press Start Clicking")

        self._build_ui()

        pyautogui.FAILSAFE = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main, text="Auto Mouse Clicker", font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        form = ttk.Frame(main)
        form.pack(fill="x")

        ttk.Label(form, text="Click interval (seconds):").grid(
            row=0, column=0, sticky="w", pady=4
        )
        ttk.Entry(form, textvariable=self.interval_var, width=12).grid(
            row=0, column=1, sticky="w", pady=4
        )

        ttk.Label(form, text="Mouse button:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            form,
            textvariable=self.button_var,
            values=["left", "right", "middle"],
            state="readonly",
            width=10,
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Number of clicks (0 = infinite):").grid(
            row=2, column=0, sticky="w", pady=4
        )
        ttk.Entry(form, textvariable=self.click_count_var, width=12).grid(
            row=2, column=1, sticky="w", pady=4
        )

        ttk.Checkbutton(
            form, text="Double click each cycle", variable=self.double_click_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        self.target_label = ttk.Label(main, text="Target: not selected")
        self.target_label.pack(anchor="w", pady=(10, 2))

        status = ttk.Label(main, textvariable=self.status_var, foreground="#1d4ed8")
        status.pack(anchor="w", pady=(0, 10))

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(6, 0))

        self.start_btn = ttk.Button(
            actions, text="Start Clicking", command=self.start_clicked
        )
        self.start_btn.pack(side="left")

        self.stop_btn = ttk.Button(
            actions, text="Stop", command=self.stop_clicked, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        ttk.Button(actions, text="Clear Target", command=self.clear_target).pack(
            side="left", padx=(8, 0)
        )

        help_text = (
            "When you press Start Clicking, this app waits for your next mouse click anywhere on the screen.\n"
            "That position is saved and used as the auto-click target.\n"
            "Move mouse to top-left corner to trigger PyAutoGUI failsafe if needed."
        )
        ttk.Label(main, text=help_text, justify="left", foreground="#475569").pack(
            anchor="w", pady=(10, 0)
        )

    def _parse_params(self) -> tuple[float, int]:
        try:
            interval = float(self.interval_var.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("Interval must be a number greater than 0.")

        try:
            total_clicks = int(self.click_count_var.get().strip())
            if total_clicks < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Number of clicks must be 0 or a positive integer.")

        return interval, total_clicks

    def start_clicked(self) -> None:
        if self.running or self.waiting_for_target:
            return

        try:
            self._parse_params()
        except ValueError as err:
            messagebox.showerror("Invalid parameters", str(err))
            return

        self.waiting_for_target = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Waiting for your next mouse click to set target...")

        listener_thread = threading.Thread(target=self._capture_next_click, daemon=True)
        listener_thread.start()

    def _capture_next_click(self) -> None:
        def on_click(x: int, y: int, button: mouse.Button, pressed: bool):
            if pressed:
                self.target_pos = (x, y)
                return False
            return True

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

        self.root.after(0, self._start_click_loop_after_target_capture)

    def _start_click_loop_after_target_capture(self) -> None:
        if self.target_pos is None:
            self.waiting_for_target = False
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.status_var.set("Target capture cancelled.")
            return

        self.waiting_for_target = False
        self.running = True
        self.stop_event.clear()

        self.target_label.config(text=f"Target: {self.target_pos}")
        self.status_var.set("Clicking started.")

        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()

    def _click_loop(self) -> None:
        interval, total_clicks = self._parse_params()
        button = self.button_var.get()
        done = 0

        while not self.stop_event.is_set():
            if self.target_pos is None:
                break

            x, y = self.target_pos
            try:
                pyautogui.click(x=x, y=y, button=button)
                if self.double_click_var.get():
                    pyautogui.click(x=x, y=y, button=button)
                pyautogui.press("ctrl")
            except pyautogui.FailSafeException:
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        "Stopped by FAILSAFE (mouse in top-left)."
                    ),
                )
                break

            done += 1
            if total_clicks > 0 and done >= total_clicks:
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        "Completed requested number of clicks."
                    ),
                )
                break

            if self.stop_event.wait(interval):
                break

        self.root.after(0, self._set_stopped_state)

    def _set_stopped_state(self) -> None:
        self.running = False
        self.waiting_for_target = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if (
            "Stopped" not in self.status_var.get()
            and "Completed" not in self.status_var.get()
        ):
            self.status_var.set("Stopped.")

    def stop_clicked(self) -> None:
        self.stop_event.set()
        if not self.running and self.waiting_for_target:
            self.status_var.set(
                "Capture in progress. Click once to finish capture, then it will stop."
            )

    def clear_target(self) -> None:
        if self.running:
            self.stop_clicked()
        self.target_pos = None
        self.target_label.config(text="Target: not selected")
        self.status_var.set("Target cleared.")

    def on_close(self) -> None:
        self.stop_event.set()
        self.root.destroy()


def capture_next_click_position() -> tuple[int, int]:
    target_pos: tuple[int, int] | None = None
    click_received = threading.Event()

    def on_click(x: int, y: int, button: mouse.Button, pressed: bool):
        nonlocal target_pos
        if pressed:
            target_pos = (x, y)
            click_received.set()
            return False
        return True

    try:
        listener = mouse.Listener(on_click=on_click)
        listener.start()
        got_click = click_received.wait(timeout=5.0)
        listener.stop()
        listener.join(timeout=1.0)
    except Exception:
        got_click = False

    if got_click and target_pos is not None:
        return target_pos

    print("No click was detected in time.")
    print("Press Enter to use current mouse position, or type coordinates like 640,360")
    screen_w, screen_h = pyautogui.size()
    print(f"Maximum coordinates on this computer: {screen_w - 1},{screen_h - 1}")
    while True:
        raw = input("Target position: ").strip()
        if not raw:
            pos = pyautogui.position()
            return (int(pos.x), int(pos.y))
        try:
            x_text, y_text = raw.split(",", maxsplit=1)
            return (int(x_text.strip()), int(y_text.strip()))
        except ValueError:
            print("Invalid format. Use x,y (example: 640,360).")


def ask_positive_float(prompt: str, default: float) -> float:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = float(raw)
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a number greater than 0.")


def ask_non_negative_int(prompt: str, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter 0 or a positive integer.")


def ask_button(prompt: str, default: str) -> str:
    valid = {"left", "right", "middle"}
    while True:
        raw = (
            input(f"{prompt} ({'/'.join(sorted(valid))}) [{default}]: ").strip().lower()
        )
        if not raw:
            return default
        if raw in valid:
            return raw
        print("Please enter left, right, or middle.")


def ask_yes_no(prompt: str, default: bool) -> bool:
    default_label = "y" if default else "n"
    while True:
        raw = input(f"{prompt} (y/n) [{default_label}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer y or n.")


def run_cli_clicker() -> None:
    pyautogui.FAILSAFE = True

    print("Tkinter is unavailable in this environment.")
    print("Running in terminal mode instead.")
    interval = ask_positive_float("Click interval in seconds", 1.0)
    button = ask_button("Mouse button", "left")
    total_clicks = ask_non_negative_int("Number of clicks (0 = infinite)", 0)
    double_click = ask_yes_no("Double click each cycle", False)

    print("\nNow click once anywhere on screen to set the target position...")
    print(
        "If no click is captured in about 12 seconds, you'll be asked for a fallback target."
    )
    target_x, target_y = capture_next_click_position()
    print(f"Saved target position: ({target_x}, {target_y})")
    print("Starting auto-clicker. Press Ctrl+C to stop.")

    done = 0
    try:
        while True:
            pyautogui.click(x=target_x, y=target_y, button=button)
            if double_click:
                pyautogui.click(x=target_x, y=target_y, button=button)
            pyautogui.press("ctrl")

            done += 1
            if total_clicks > 0 and done >= total_clicks:
                print("Completed requested number of clicks.")
                break

            time_wait = interval
            threading.Event().wait(time_wait)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except pyautogui.FailSafeException:
        print("\nStopped by FAILSAFE (mouse moved to top-left corner).")


def main() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        if (
            "init.tcl" in str(exc).lower()
            or "can't find a usable init.tcl" in str(exc).lower()
        ):
            run_cli_clicker()
            return
        raise

    MouseClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
