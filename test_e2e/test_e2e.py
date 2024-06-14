import logging
from operator import contains
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
    # Preparacion
    # Navegar a telegram
    driver.get("https://web.telegram.org")

    # Logueo manual
    logger.info("esperando loguearse")
    time.sleep(20)
    logger.info("arranquemos")

    # TEST GENERANDO UN PEDIDO
    # Entramos en el chat del grupo
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys("@PediTest")
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)
    search_box.send_keys(Keys.RETURN)

    # Enviamos el comando para iniciar un pedido
    message_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@dir="auto"]'))
    )
    message_box.send_keys("/iniciar_pedido")
    message_box.send_keys(Keys.RETURN)
    time.sleep(3)
    
    # Seleccionamos Contactar al bot
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Contactar bot"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos Realizar pedido individual
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Realizar pedido individual"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos restaurante
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Unq King"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos producto
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Lomo Con Queso"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos cantidad
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="3"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos Finalizar pedidos individuales
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedidos individuales"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Volvemos al chat del grupo
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys("@PediTest")
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)
    search_box.send_keys(Keys.RETURN)

    # Seleccionamos Finalizar pedido
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedido"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Verificamos que se realizo el pedido de 3 Lomo Con Queso
    message = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//div[@class="text-content clearfix with-meta"][@dir="auto"]'))
    )
    message_text = message[-1].text

    assert contains(message_text, "Lomo Con Queso: 3")

    # TEST GENERANDO UN PEDIDO UTILIZANDO LA PAGINACION
    # Enviamos el comando para iniciar un pedido
    message_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@dir="auto"]'))
    )
    message_box.send_keys("/iniciar_pedido")
    message_box.send_keys(Keys.RETURN)
    time.sleep(3)
    
    # Seleccionamos Contactar al bot
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Contactar bot"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos Realizar pedido individual
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Realizar pedido individual"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos restaurante
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Siguiente "]]'))
    )
    button[-1].click()
    time.sleep(3)
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Cope"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos producto
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Siguiente "]]'))
    )
    button[-1].click()
    time.sleep(3)
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Siguiente "]]'))
    )
    button[-1].click()
    time.sleep(3)
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()=" Anterior"]]'))
    )
    button[-1].click()
    time.sleep(3)
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Gran Cope"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos cantidad
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="1"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Seleccionamos Finalizar pedidos individuales
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedidos individuales"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Volvemos al chat del grupo
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]'))
    )
    search_box.send_keys("@PediTest")
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)
    search_box.send_keys(Keys.RETURN)

    # Seleccionamos Finalizar pedido
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//button[@class="Button tiny primary has-ripple" and .//span[text()="Finalizar pedido"]]'))
    )
    button[-1].click()
    time.sleep(3)

    # Verificamos que se realizo el pedido de 1 Gran Cope
    message = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//div[@class="text-content clearfix with-meta"][@dir="auto"]'))
    )
    message_text = message[-1].text

    assert contains(message_text, "Gran Cope: 1")

finally:
    # Cerrar el navegador
    time.sleep(10)
    driver.quit()