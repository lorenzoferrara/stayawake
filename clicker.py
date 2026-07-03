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
        # Let Tk size the window from content and keep a safe minimum size.
        self.root.minsize(430, 320)
        self.root.resizable(True, True)

        # Runtime state
        self.running = False
        self.waiting_for_target = False
        self.target_pos: tuple[int, int] | None = None
        self.click_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self.interval_var = tk.StringVar(value="4.0")
        self.button_var = tk.StringVar(value="left")
        self.double_click_var = tk.BooleanVar(value=False)
        self.return_mouse_var = tk.BooleanVar(value=True)
        self.click_count_var = tk.StringVar(value="0")  # 0 means infinite
        self.status_var = tk.StringVar(value="Set parameters and press Start Clicking")

        self._build_ui()
        self._refresh_action_button_theme()

        pyautogui.FAILSAFE = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        self.root.configure(bg="#f4f7f5")

        main = tk.Frame(self.root, bg="#f4f7f5", padx=16, pady=16)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Auto Mouse Clicker",
            bg="#f4f7f5",
            fg="#1f2937",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        tk.Label(
            main,
            text="Simple, reliable clicks with safer controls",
            bg="#f4f7f5",
            fg="#64748b",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 12))

        form = tk.Frame(
            main,
            bg="#ffffff",
            highlightbackground="#dbe4de",
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        form.pack(fill="x")

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=0)

        tk.Label(
            form,
            text="Click interval (seconds):",
            bg="#ffffff",
            fg="#334155",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.interval_var, width=14).grid(
            row=0, column=1, sticky="e", pady=6
        )

        tk.Label(
            form,
            text="Mouse button:",
            bg="#ffffff",
            fg="#334155",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(
            form,
            textvariable=self.button_var,
            values=["left", "right", "middle"],
            state="readonly",
            width=12,
        ).grid(row=1, column=1, sticky="e", pady=6)

        tk.Label(
            form,
            text="Number of clicks (0 = infinite):",
            bg="#ffffff",
            fg="#334155",
            font=("Segoe UI", 10),
        ).grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.click_count_var, width=14).grid(
            row=2, column=1, sticky="e", pady=6
        )

        ttk.Checkbutton(
            form, text="Double click each cycle", variable=self.double_click_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 4))

        ttk.Checkbutton(
            form,
            text="Return mouse to original position",
            variable=self.return_mouse_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(2, 4))

        self.target_label = tk.Label(
            main,
            text="Target: not selected",
            bg="#f4f7f5",
            fg="#334155",
            font=("Segoe UI", 10),
        )
        self.target_label.pack(anchor="w", pady=(10, 2))

        tk.Label(
            main,
            textvariable=self.status_var,
            bg="#f4f7f5",
            fg="#0f766e",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        actions = tk.Frame(main, bg="#f4f7f5")
        actions.pack(fill="x", pady=(2, 0))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)

        self.start_btn = tk.Button(
            actions,
            text="Start Clicking",
            command=self.start_clicked,
            bg="#bddfc1",
            fg="#16351b",
            activebackground="#a9d2ae",
            activeforeground="#112b16",
            relief="flat",
            padx=8,
            pady=8,
        )
        self.start_btn.grid(row=0, column=0, sticky="ew")

        self.resume_btn = tk.Button(
            actions,
            text="Resume",
            command=self.resume_clicked,
            bg="#9fc6ea",
            fg="#17324b",
            activebackground="#8bb8df",
            activeforeground="#11283c",
            disabledforeground="#5d7488",
            relief="flat",
            padx=8,
            pady=8,
        )
        self.resume_btn.grid(row=0, column=1, padx=8, sticky="ew")

        self.stop_btn = tk.Button(
            actions,
            text="Stop",
            command=self.stop_clicked,
            state="disabled",
            bg="#e49c9c",
            fg="#4a1b1b",
            activebackground="#e2adad",
            activeforeground="#3b1515",
            disabledforeground="#6b3b3b",
            relief="flat",
            padx=8,
            pady=8,
        )
        self.stop_btn.grid(row=0, column=2, sticky="ew")

        help_text = (
            "When you press Start Clicking, this app waits for your next mouse click anywhere on the screen.\n"
            "That position is saved and used as the auto-click target.\n"
            "Move mouse to top-left corner to trigger PyAutoGUI failsafe if needed."
        )
        tk.Label(
            main,
            text=help_text,
            justify="left",
            bg="#f4f7f5",
            fg="#64748b",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(12, 0))

    def _refresh_action_button_theme(self) -> None:
        clicker_on = self.running or self.waiting_for_target

        if clicker_on:
            self.start_btn.config(
                bg="#d7e6d9",
                fg="#38513d",
                activebackground="#c9dccd",
                activeforeground="#324737",
                disabledforeground="#6a8070",
            )
            self.resume_btn.config(
                bg="#d9dde2",
                fg="#59636f",
                activebackground="#cbd2da",
                activeforeground="#4d5661",
                disabledforeground="#7b8794",
            )
            self.stop_btn.config(
                bg="#e8b5b5",
                fg="#4a1b1b",
                activebackground="#dda4a4",
                activeforeground="#3b1515",
                disabledforeground="#7d5252",
            )
        else:
            self.start_btn.config(
                bg="#bddfc1",
                fg="#16351b",
                activebackground="#a9d2ae",
                activeforeground="#112b16",
                disabledforeground="#5f7b63",
            )
            self.resume_btn.config(
                bg="#9fc6ea",
                fg="#17324b",
                activebackground="#8bb8df",
                activeforeground="#11283c",
                disabledforeground="#5d7488",
            )
            self.stop_btn.config(
                bg="#d9dde2",
                fg="#4b5563",
                activebackground="#cbd2da",
                activeforeground="#374151",
                disabledforeground="#6b7280",
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
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._refresh_action_button_theme()
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
            self.resume_btn.config(state="normal" if self.target_pos is not None else "disabled")
            self.stop_btn.config(state="disabled")
            self._refresh_action_button_theme()
            self.status_var.set("Target capture cancelled.")
            return

        self.target_label.config(text=f"Target: {self.target_pos}")
        self.status_var.set("Clicking started.")
        self._start_clicking_with_current_target()

    def _start_clicking_with_current_target(self) -> None:
        self.waiting_for_target = False
        self.running = True
        self.stop_event.clear()
        self.start_btn.config(state="normal")
        self.resume_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self._refresh_action_button_theme()

        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()

    def resume_clicked(self) -> None:
        if self.running or self.waiting_for_target:
            return

        if self.target_pos is None:
            messagebox.showinfo("No target", "Set a target first by using Start Clicking.")
            return

        self.target_label.config(text=f"Target: {self.target_pos}")
        self.status_var.set("Clicking resumed.")
        self._start_clicking_with_current_target()

    def _click_loop(self) -> None:
        interval, total_clicks = self._parse_params()
        button = self.button_var.get()
        return_mouse = self.return_mouse_var.get()
        done = 0

        while not self.stop_event.is_set():
            if self.target_pos is None:
                break

            x, y = self.target_pos
            try:
                original_pos = pyautogui.position() if return_mouse else None
                pyautogui.click(x=x, y=y, button=button)
                if self.double_click_var.get():
                    pyautogui.click(x=x, y=y, button=button)
                pyautogui.press("ctrl")
                if original_pos is not None:
                    pyautogui.moveTo(original_pos.x, original_pos.y)
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
        self.resume_btn.config(state="normal" if self.target_pos is not None else "disabled")
        self.stop_btn.config(state="disabled")
        self._refresh_action_button_theme()
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
    interval = ask_positive_float("Click interval in seconds", 4)
    button = ask_button("Mouse button", "left")
    total_clicks = ask_non_negative_int("Number of clicks (0 = infinite)", 0)
    double_click = ask_yes_no("Double click each cycle", False)
    return_mouse = ask_yes_no("Return mouse to original position after each click", True)

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
            original_pos = pyautogui.position() if return_mouse else None
            pyautogui.click(x=target_x, y=target_y, button=button)
            if double_click:
                pyautogui.click(x=target_x, y=target_y, button=button)
            pyautogui.press("ctrl")
            if original_pos is not None:
                pyautogui.moveTo(original_pos.x, original_pos.y)

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
