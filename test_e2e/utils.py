from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def go_to_group_chat(driver, group_name: str):
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys(f"@{group_name}")
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)
    search_box.send_keys(Keys.RETURN)


def send_command(driver, command: str):
    message_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@dir="auto"]'))
    )
    message_box.send_keys(command)
    message_box.send_keys(Keys.RETURN)
    time.sleep(3)


def click_button(driver, button_name: str):
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, f'//button[@class="Button tiny primary has-ripple" and .//span[text()="{button_name}"]]'))
    )
    button[-1].click()
    time.sleep(3)


def get_the_last_message_text(driver):
    message = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//div[@class="text-content clearfix with-meta"][@dir="auto"]'))
    )
    return message[-1].text