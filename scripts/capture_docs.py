import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,1200")
options.add_argument("--force-device-scale-factor=1")
options.add_argument("--disable-gpu")
driver = webdriver.Edge(options=options)
driver.set_window_size(1440, 1200)
driver.get("http://127.0.0.1:3000/documentation")
WebDriverWait(driver, 20).until(lambda d: "Security limitations" in d.find_element(By.TAG_NAME, "body").text)
driver.execute_script("document.getElementById('limits').scrollIntoView({block:'start'})")
time.sleep(0.5)
path = Path(r"c:\Users\kamod\OneDrive\Desktop\CIS-030(Main)\report_images\14-documentation.png")
driver.save_screenshot(str(path))
driver.quit()
print(path)
