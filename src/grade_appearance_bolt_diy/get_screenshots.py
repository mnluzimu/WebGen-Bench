"""
scroll_shooter.py
-----------------
Save up‑to‑three vertical “strips” of a web page as PNG files.

Usage
-----
$ python scroll_shooter.py https://example.com  # saves shot_1.png … shot_n.png
"""

import math
import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import tempfile


def make_driver(width: int = 1024, height: int = 768) -> webdriver.Chrome:
    """Create a headless Chrome WebDriver with a fixed viewport."""
    opts = Options()
    opts.add_argument("--headless=new")        # Chrome 109+
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--window-size={width},{height}")
    
    temp_user_data_dir = tempfile.mkdtemp()
    opts.add_argument(f"--user-data-dir={temp_user_data_dir}")

    return webdriver.Chrome(options=opts)


def capture_scroll_screenshots(url: str,
                               out_dir: str = "shots",
                               max_shots: int = 3,
                               pause: float = 0.4,
                               viewport_height: int = 768) -> None:
    """Scroll the page, saving at most `max_shots` screenshots."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    driver = make_driver(height=viewport_height)

    try:
        driver.get(url)
    except Exception as e:
        print(f"Error loading page: {e}")
        driver.quit()
        return

    # Give the page a moment to settle.
    time.sleep(pause)

    total_height = driver.execute_script("return document.body.scrollHeight")
    n_required   = math.ceil(total_height / viewport_height)
    n_to_take    = min(max_shots, n_required)

    for idx in range(n_to_take):
        # File names: shot_1.png, shot_2.png, …
        fname = os.path.join(out_dir, f"shot_{idx + 1}.png")
        driver.save_screenshot(fname)
        print(f"Saved {fname}")

        # Break early if we're already at (or past) the bottom.
        if (idx + 1) == n_to_take:
            break

        # Scroll down exactly one viewport height.
        driver.execute_script("window.scrollBy(0, arguments[0]);", viewport_height)
        time.sleep(pause)  # wait for lazy‑loaded images, JS, etc.

    driver.quit()
    

def __test():
    target_url  = "http://localhost:3000/"
    output_dir  = r"F:\research\bolt\APP-Bench\src\grade_appearance\shots"
    capture_scroll_screenshots(target_url, output_dir, max_shots=3, pause=0.4, viewport_height=768)


if __name__ == "__main__":
    __test()