import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configurar el driver (asegúrate de que chromedriver esté en tu PATH)
driver = webdriver.Chrome()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

try:
    # Test generando un pedido
    # Navegar a telegram
    driver.get("https://web.telegram.org")

    # Logueo manual
    logger.info("esperando loguearse")
    time.sleep(30)
    logger.info("arranquemos")

    # Entramos en el chat del grupo
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys("@PediTest")
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    search_box.send_keys(Keys.RETURN)

    # Enviamos el comando para iniciar un pedido
    message_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@dir="auto"]'))
    )
    message_box.send_keys("/iniciar_pedido")
    message_box.send_keys(Keys.RETURN)
    time.sleep(10)
    
    # Seleccionamos Contactar al bot
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Contactar bot"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Seleccionamos Realizar pedido individual
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Realizar pedido individual"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Seleccionamos restaurante
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Unq King"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Seleccionamos producto
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Papas Fritas"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Seleccionamos cantidad
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="3"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Seleccionamos Finalizar pedidos individuales
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedidos individuales"]]'))
    )
    button[0].click()
    time.sleep(10)

    # Volvemos al chat del grupo
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys("@PediTest")
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    search_box.send_keys(Keys.RETURN)

    # Seleccionamos Finalizar pedido
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedido"]]'))
    )
    button[0].click()
    time.sleep(10)

    assert "No results found." not in driver.page_source

finally:
    # Cerrar el navegador
    time.sleep(10)
    driver.quit()