import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def automatic_web_gen(idx, instruction, download_dir="downloads", url="http://localhost:5173/",
    desired_model="/mnt/cache/sharemath/models/qwen/Qwen2.5-Coder-32B-Instruct", provider="OpenAILike"):
    print(f"Running automatic_web_gen with idx={idx}, instruction='{instruction}', download_dir='{download_dir}', url='{url}', desired_model='{desired_model}', provider='{provider}'")
    # ---------------------------------------
    # 1) Set up Chrome & your download folder
    # ---------------------------------------
    # If Chrome is set to download automatically to, e.g., "C:/Users/<user>/Downloads":
    download_dir = os.path.abspath(download_dir) # <-- adjust as needed
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    if os.path.exists(os.path.join(download_dir, f"{idx:06d}.json")) and os.path.exists(os.path.join(download_dir, f"{idx:06d}.zip")):
        print(f"Files {idx:06d}.json and {idx:06d}.zip already exist. Skipping download.")
        return

    # If you want to explicitly configure the download folder and disable popups:
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()

    # --- Headless mode ---
    # For Chrome ≥ 109, “--headless=new” is recommended.
    # If you’re on an older version, use "--headless" instead.
    # chrome_options.add_argument("--headless=new")     # <‑‑ headless flag
    chrome_options.add_argument("--window-size=1920,1080")  # helpful for some UIs

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(2)

        #
        # --- STEP A: Select the first <select> dropdown
        #
        model_select = Select(driver.find_element(
            By.CSS_SELECTOR, 
            "div.mb-2.flex select.flex-1.p-2.rounded-lg.border"
        ))
        model_select.select_by_value(provider)  

        # --- STEP B: open the custom combobox ---
        combobox = driver.find_element(
            By.CSS_SELECTOR,
            'div[role="combobox"].w-full.p-2.rounded-lg.cursor-pointer'
        )
        combobox.click()

        wait = WebDriverWait(driver, 30)

        # wait until the listbox itself is visible
        wait.until(EC.visibility_of_element_located((By.ID, "model-listbox")))

        # build a locator for the exact option text you want
        option_locator = (
            By.XPATH,
            f'//div[@id="model-listbox"]//div[@role="option" and '
            f'normalize-space()="{desired_model}"]'
        )

        # wait until that option is clickable, then click it
        wait.until(EC.element_to_be_clickable(option_locator)).click()

        #
        # --- STEP C: Enter text in the chat box & press Enter
        #
        text_box = driver.find_element(By.CSS_SELECTOR, "textarea")
        text_box.clear()
        text_box.send_keys(instruction)
        text_box.send_keys(Keys.ENTER)

        #
        # --- STEP D: Wait for both conditions:
        #    1) "Response Generated" to appear
        #    2) "Download Code" button to disappear
        #
        try:
            wait = WebDriverWait(driver, 1200)

            # Condition 1: "Response Generated" appears
            wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@class='flex text-sm gap-3' and contains(., 'Response Generated')]")
                )
            )

            # Condition 2: "Download Code" button disappears
            # (e.g. if it was visible earlier and is removed or hidden once the code is fully processed)
            # wait.until(
            #     EC.invisibility_of_element_located(
            #         (By.XPATH, "//button[contains(text(), 'Download Code')]")
            #     )
            # )
        except:
            print("Timed out waiting for response or button state change.")

        time.sleep(10)

        #
        # --- STEP E: Click the "Code" button
        #
        code_button = driver.find_element(
            By.XPATH, 
            "//button[.//span[text()='Code']]"
        )
        code_button.click()
        time.sleep(1)

        #
        # --- STEP F: Download Code, rename to {idx:06d}.zip
        #
        files_before = set(os.listdir(download_dir))
        download_code_button = driver.find_element(
            By.XPATH, 
            "//button[contains(text(), 'Download Code')]"
        )
        download_code_button.click()
        time.sleep(5)  # Wait for the code download

        files_after = set(os.listdir(download_dir))
        new_files = files_after - files_before
        if len(new_files) == 1:
            downloaded_file = new_files.pop()
            old_path = os.path.join(download_dir, downloaded_file)
            zip_name = f"{idx:06d}.zip"
            new_path = os.path.join(download_dir, zip_name)
            if os.path.exists(new_path):
                os.remove(new_path)  # Remove old file if it exists
            os.rename(old_path, new_path)
            print(f"Renamed code file to: {new_path}")
        else:
            print("Could not uniquely identify the downloaded code file.")

        #
        # --- STEP G: Export Chat -> rename to {idx:06d}.json
        #
        files_before = set(os.listdir(download_dir))
        export_chat_button = driver.find_element(
            By.XPATH,
            "//button[@title='Export Chat']"
        )
        export_chat_button.click()
        time.sleep(5)  # Wait for the chat download

        files_after = set(os.listdir(download_dir))
        new_files = files_after - files_before
        if len(new_files) == 1:
            downloaded_file = new_files.pop()
            old_path = os.path.join(download_dir, downloaded_file)
            json_name = f"{idx:06d}.json"
            new_path = os.path.join(download_dir, json_name)
            if os.path.exists(new_path):
                os.remove(new_path)  # Remove old file if it exists
            os.rename(old_path, new_path)
            print(f"Renamed chat file to: {new_path}")
        else:
            print("Could not uniquely identify the downloaded chat file.")

        time.sleep(1)

    finally:
        driver.quit()

if __name__ == "__main__":
    main(idx=1)
