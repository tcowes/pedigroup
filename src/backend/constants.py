from telegram import BotCommand

HEADERS_FROM_CSV = ["Restaurant", "Product", "Price"]

# Comandos del bot
START_ORDER_COMMAND_DESC = "Solo puede llamarse desde grupos. Inicia un pedido grupal."
START_ORDER_COMMAND = BotCommand(command="iniciar_pedido", description=START_ORDER_COMMAND_DESC)
LOAD_CSV_COMMAND_DESC = (
    "Solo puede llamarse desde grupos. Arroja un mensaje al cual se le puede responder con un archivo .csv que "
    f"respete las columnas '{','.join(HEADERS_FROM_CSV)}' para cargar datos de restaurantes y sus productos."
)
LOAD_CSV_COMMAND = BotCommand(command="cargar_csv", description=LOAD_CSV_COMMAND_DESC)
HELP_COMMAND_DESC = "Para ver una explicación básica del funcionamiento del bot."
HELP_COMMAND = BotCommand(command="help", description=HELP_COMMAND_DESC)

ALL_COMMANDS = [START_ORDER_COMMAND, LOAD_CSV_COMMAND, HELP_COMMAND]

# Mensajes que arroja el bot
HELP_MESSAGE = (
    "Para iniciar pedidos con el bot primero hay que cargar datos de restaurantes y productos para un grupo. Esto se"
    " hace con el llamado a /cargar_csv, allí se dan instrucciones mas detalladas sobre la carga de archivos.\n\n"
    "Una vez que el grupo conoce restaurantes y productos, se pueden iniciar pedidos con /iniciar_pedido. A partir de"
    " ahí, el bot va indicando cuales son los pasos a seguir.\n\n"
    f"Listado de comandos:\n{''.join([f' - /{bot_com.command} {bot_com.description}\n' for bot_com in ALL_COMMANDS])}"
)
USER_STARTED_ORDER_MESSAGE = lambda username: (
    f"{username} inició un pedido!\n\nQuienes quieran pedir deben contactarse conmigo mediante un chat privado "
    "clickeando el siguiente botón ↓"
)
IN_COURSE_ORDER_MESSAGE = "Ya hay un pedido en curso, finalizar clickeando el boton _Finalizar pedido_"
ONLY_IN_GROUPS_MESSAGE = "Este comando solo puede llamarse desde un grupo."
NO_ORDER_INITIATED_MESSAGE = (
    "Este comando solo puede llamarse una vez que alguien haya iniciado un pedido en un grupo con /iniciar_pedido."
)
NO_RESTAURANTS_FOUND_MESSAGE = (
    "Aún no se cargaron restaurantes en tu grupo, podés hacerlo siguiendo las instrucciones del bot en el grupo"
)
PICK_RESTAURANTS_MESSAGE = "Seleccioná a que restaurante te gustaría pedir:"
PICK_PRODUCTS_MESSAGE = "Seleccioná que producto te gustaría pedir:"

# Texto de botones
NEXT_BUTTON = "Siguiente ▶"
PREVIOUS_BUTTON = "◀ Anterior"
ADD_PRODUCTS_BUTTON = "Añadir mas pedidos"
FINISH_INDIVIDUAL_ORDERS = "Finalizar pedidos individuales"

# Relacionado con CSV
CSV_LOAD_EXCEPTION_MESSAGE = (
    f"El csv ingresado no respeta el formato de las columnas. Estas deberían ser '{','.join(HEADERS_FROM_CSV)}'"
)
CSV_LOAD_UNKNOWN_EXCEPTION_MESSAGE = "El csv ingresado no pudo ser procesado. Error desconocido..."
CSV_SUCCESSFULLY_PROCESSED = lambda restaurants, products, ommited_rows: (
    "El csv ingresado fue procesado correctamente!\n\n"
    f" - Restaurants creados: {restaurants}.\n - Productos creados: {products}."
    f"{f'\n - Filas omitidas: {ommited_rows}.' if ommited_rows > 0 else ''}"
)
CSV_INSTRUCTIONS_MESSAGE = (
    "Genial!, ahora necesito que respondas a este mensaje adjuntando el archivo CSV que queres cargar, para eso tenes "
    "que tocar el botón 📎."
)
