import logging
from operator import contains
from selenium import webdriver
import time

from utils import click_button, get_the_last_message_text, go_to_group_chat, send_command

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
    go_to_group_chat(driver, "PediTest")
    send_command(driver, "/iniciar_pedido")
    click_button(driver, "Contactar bot")
    click_button(driver, "Realizar pedido individual")
    click_button(driver, "Unq King")
    click_button(driver, "Lomo Con Queso")
    click_button(driver, "3")
    click_button(driver, "Finalizar pedidos individuales")
    go_to_group_chat(driver, "PediTest")
    click_button(driver, "Finalizar pedido")

    # Verificamos que se realizo el pedido de 3 Lomo Con Queso
    message_text = get_the_last_message_text(driver)

    assert contains(message_text, "Lomo Con Queso: 3")


    # TEST GENERANDO UN PEDIDO UTILIZANDO LA PAGINACION
    send_command(driver, "/iniciar_pedido")
    click_button(driver, "Contactar bot")
    click_button(driver, "Realizar pedido individual")
    # Seleccionamos restaurante
    click_button(driver, "Siguiente ")
    click_button(driver, "Cope")
    # Seleccionamos producto
    click_button(driver, "Siguiente ")
    click_button(driver, "Siguiente ")
    click_button(driver, " Anterior")
    click_button(driver, "Gran Cope")
    click_button(driver, "1")
    click_button(driver, "Finalizar pedidos individuales")
    go_to_group_chat(driver, "PediTest")
    click_button(driver, "Finalizar pedido")

    # Verificamos que se realizo el pedido de 1 Gran Cope
    message_text = get_the_last_message_text(driver)

    assert contains(message_text, "Gran Cope: 1")


    # TEST GENERANDO UN PEDIDO MODIFICANDOLO EN EL PROCESO Y AL FINALIZARLO
    send_command(driver, "/iniciar_pedido")
    click_button(driver, "Contactar bot")
    click_button(driver, "Realizar pedido individual")
    # Seleccionamos restaurante y volvemos para modificar
    click_button(driver, "Unq King")
    click_button(driver, "Volver a selección de restaurantes")
    click_button(driver, "Unqtaza")
    # Seleccionamos producto y volvemos para modificar
    click_button(driver, "Milanesa De Cerdo")
    click_button(driver, "Volver a selección de productos")
    click_button(driver, "Milanesa De Pollo")
    click_button(driver, "5")
    # Modificamos el producto y la cantidad
    click_button(driver, "Modificar producto")
    click_button(driver, "Milanesa De Cerdo")
    click_button(driver, "Modificar cantidad")
    click_button(driver, "2")
    click_button(driver, "Finalizar pedidos individuales")
    go_to_group_chat(driver, "PediTest")
    click_button(driver, "Finalizar pedido")

    # Verificamos que se realizo el pedido de 2 Milanesa De Cerdo
    message_text = get_the_last_message_text(driver)

    assert contains(message_text, "Milanesa De Cerdo: 2")


    # TEST PEDIMOS EL HISTORIAL Y VEMOS QUE ESTEN LOS 3 PEDIDOS HECHOS
    # Enviamos el comando para ver el historial
    send_command(driver, "/historial_de_pedidos")

    # Verificamos que se realizaron los 3 pedidos
    message_text = get_the_last_message_text(driver)

    assert contains(message_text, "Lomo Con Queso: 3")
    assert contains(message_text, "Gran Cope: 1")
    assert contains(message_text, "Milanesa De Cerdo: 2")

finally:
    # Cerrar el navegador
    time.sleep(10)
    driver.quit()