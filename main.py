import pyautogui
import time
import sys


def main():
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to stop safely
    print("Mover started")

    mytime = 10  # seconds between checks
    pyautogui.moveTo(1, 1)
    last_pos = pyautogui.position()
    working_delta = 0

    starting_hour = time.localtime().tm_hour
    print(starting_hour)
    if starting_hour < 13:
        day_part = "morning"
    else:
        day_part = "afternoon"

    while True:
        hour = time.localtime().tm_hour

        # Work hours: before 13:00 or between 14:00–18:00
        if hour >= 13 and day_part == "morning":
            break
        if hour >= 18:
            break

        time.sleep(mytime)

        current_pos = pyautogui.position()

        screen_width, screen_height = pyautogui.size()
        corner_pos = (1, 1)
        left_pos = (1, screen_height // 2)

        if current_pos == corner_pos:
            pyautogui.moveTo(*left_pos)
            pyautogui.press('ctrl')
        elif current_pos == last_pos:
            pyautogui.moveTo(*corner_pos)
            pyautogui.press('ctrl')
            working_delta = 0
        else:
            working_delta = mytime * 2

        last_pos = current_pos

        time.sleep(mytime + working_delta)

    if hour == 13:
        print("Time for lunch!")
    elif hour >= 18:
        print("Time to go home!")
    else:
        print("Script stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(0)
