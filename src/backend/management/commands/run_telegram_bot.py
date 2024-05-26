from typing import Dict

from django.conf import settings

from backend.constants import *
from backend.exceptions import WrongHeadersForCsv
from backend.models import Group, Order, Product, Restaurant

import logging
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    Application,
)

from backend.service import (
    create_entities_through_csv,
    register_group_and_user_if_required,
    register_user_order,
    register_user_and_add_to_group_if_required,
    register_group_order
)
from django.core.management.base import BaseCommand

from backend.utils import format_order

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start telegram bot"

    def handle(self, *args, **options):
        start_bot()


# Variable global para trackear el estado de un pedido.
orders_initiated: Dict[int, bool] = {}
# Variable global para ir almacenando los pedidos
current_user_orders: Dict[int, list[Order]] = {}

MENU, TYPE_SELECTION, QUANTITY = range(3)


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text(ONLY_IN_GROUPS_MESSAGE)
        return

    group = update.message.chat
    user = update.message.from_user
    group_id = update.message.chat_id

    register_group_and_user_if_required(group, user)

    logger.info(f"{user.first_name} ({user.id}) {group.title} ({group_id}) called {'/iniciar_pedido'}")

    global orders_initiated
    global current_user_orders
    if not orders_initiated.get(group_id):
        orders_initiated[group_id] = False
        current_user_orders[group_id] = []
    reply_markup = InlineKeyboardMarkup([])
    match orders_initiated.get(group_id):
        case False:
            message = USER_STARTED_ORDER_MESSAGE(user.first_name)
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contactar bot", url=f"t.me/{context.bot.username}?start={group_id}")],
                 [InlineKeyboardButton("Finalizar pedido", callback_data=f"Finalizar pedido {group_id}")]])
            orders_initiated[group_id] = True
        case True:
            message = IN_COURSE_ORDER_MESSAGE

    await context.bot.send_message(group_id, message, reply_markup=reply_markup, parse_mode="Markdown")


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orders_initiated
    global current_user_orders

    query = update.callback_query
    group_id = int(query.data.removeprefix("Finalizar pedido "))
    group = Group.objects.get(id_app=group_id)  # TODO: Esta query tendría que extraerse a service
    user = query.from_user
    register_user_and_add_to_group_if_required(user, group_id)

    logger.info(f"{user.first_name} ({user.id}) {group.name} ({group_id}) finished the current order")
    group_order = current_user_orders[group_id]
    current_user_orders[group_id] = []
    orders_initiated[group_id] = False

    register_group_order(group, group_order)
    formatted_order = format_order(group_order)
    await query.edit_message_text(
        f"{user.first_name} finalizó el pedido!\n\nEn total se pidieron:\n{formatted_order}", reply_markup=None
    )


async def start_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_with_group_id = update.message.text
    group_id = int(message_with_group_id.removeprefix("/start "))
    pedigroup_group = Group.objects.get(id_app=group_id)
    group_name = pedigroup_group.name
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Realizar pedido individual", callback_data=f"pedir {group_id} {group_name}")]])
    await update.message.reply_text(f"Bienvenido a PediGroup, queres añadir pedidos individuales para _{group_name}_?",
                                    reply_markup=reply_markup, parse_mode="Markdown")


async def show_initial_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    message_with_group_id_and_name = query.data.removeprefix("pedir ")
    message_with_group_id_and_name = message_with_group_id_and_name.split(" ")
    group_id = int(message_with_group_id_and_name[0])
    group_name = ' '.join(message_with_group_id_and_name[1:])
    global orders_initiated
    if not orders_initiated[group_id]:
        await update.message.reply_text(NO_ORDER_INITIATED_MESSAGE)
        return

    restaurants_count = Restaurant.objects.filter(group__id_app=group_id).count()
    context.user_data['current_page'] = 0
    context.user_data['quantity_of_items'] = restaurants_count

    if restaurants_count > 0:
        reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, "Restaurants")
        await query.message.reply_text(PICK_RESTAURANTS_MESSAGE, reply_markup=reply_markup)
    else:
        await query.message.reply_text(NO_RESTAURANTS_FOUND_MESSAGE)
        return ConversationHandler.END
    return MENU


async def show_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reply_markup = select_page_to_show(update, context, "Restaurants")
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return MENU


async def show_initial_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    message_with_restaurant_id_flag_group_id_and_name = query.data.removeprefix("menu ")
    message_with_restaurant_id_flag_group_id_and_name = message_with_restaurant_id_flag_group_id_and_name.split(" ")
    restaurant_id = message_with_restaurant_id_flag_group_id_and_name[0]
    restaurant = Restaurant.objects.get(id=restaurant_id)
    if_first_message = message_with_restaurant_id_flag_group_id_and_name[1]
    group_id = int(message_with_restaurant_id_flag_group_id_and_name[2])
    group_name = ' '.join(message_with_restaurant_id_flag_group_id_and_name[3:])

    if if_first_message == "YES":
        restaurant_name = restaurant.name
        await context.bot.edit_message_text(text=f"Los siguientes pedidos son al restaurante _{restaurant_name}_",
                                            chat_id=query.message.chat_id,
                                            message_id=query.message.message_id,
                                            reply_markup=None,
                                            parse_mode="Markdown")

    context.user_data['restaurant_id'] = restaurant_id
    context.user_data['current_page'] = 0
    context.user_data['quantity_of_items'] = restaurant.products_quantity()
    reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, "Products")

    await query.message.reply_text(PICK_PRODUCTS_MESSAGE, reply_markup=reply_markup)

    return TYPE_SELECTION


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reply_markup = select_page_to_show(update, context, "Products")
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return TYPE_SELECTION


def select_page_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE, items_to_paginate):
    query = update.callback_query
    page_movement_with_group_id_and_name = query.data.split(" ")
    page_movement = page_movement_with_group_id_and_name[0]
    group_id = int(page_movement_with_group_id_and_name[1])
    group_name = ' '.join(page_movement_with_group_id_and_name[2:])
    page = context.user_data['current_page']

    if page_movement == "Siguiente":
        context.user_data['current_page'] = page + 1
    else:
        context.user_data['current_page'] = page - 1

    reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, items_to_paginate)
    return reply_markup


def show_menu_or_restaurant_page(context: ContextTypes.DEFAULT_TYPE, group_id, group_name, items_to_show):
    page = context.user_data['current_page']
    quantity_of_items = context.user_data['quantity_of_items']
    first_item = page * 5
    last_item = first_item + 5
    keyboard = []
    if items_to_show == "Restaurants":
        restaurants = [rest for rest in Restaurant.objects.filter(group__id_app=group_id)[first_item:last_item]]
        for restaurant in restaurants:
            keyboard.append([InlineKeyboardButton(restaurant.name,
                                                  callback_data=f"menu {restaurant.id} YES {group_id} {group_name}")])
    elif items_to_show == "Products":
        restaurant_id = context.user_data['restaurant_id']
        products = [prod for prod in Product.objects.filter(restaurant__id=restaurant_id)[first_item:last_item]]
        for product in products:
            keyboard.append([InlineKeyboardButton(product.name, callback_data=f"{product.id} {group_id} {group_name}")])

    previous_button = InlineKeyboardButton(PREVIOUS_BUTTON, callback_data=f"Anterior {group_id} {group_name}")
    next_button = InlineKeyboardButton(NEXT_BUTTON, callback_data=f"Siguiente {group_id} {group_name}")
    if page == 0 and quantity_of_items > last_item:
        keyboard.append([next_button])
    elif page > 0 and quantity_of_items > last_item:
        keyboard.append([previous_button, next_button])
    elif page > 0 and quantity_of_items <= last_item:
        keyboard.append([previous_button])

    return InlineKeyboardMarkup(keyboard)


async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id_with_group_id_and_name = query.data.split(" ")
    product_id = int(product_id_with_group_id_and_name[0])
    pedigroup_product = Product.objects.get(id=product_id)
    group_id = product_id_with_group_id_and_name[1]
    group_name = ' '.join(product_id_with_group_id_and_name[2:])

    context.user_data['product_id'] = product_id

    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([InlineKeyboardButton(i, callback_data=f"{i} {group_id} {group_name}"),
                         InlineKeyboardButton(i + 1, callback_data=f"{i + 1} {group_id} {group_name}"),
                         InlineKeyboardButton(i + 2, callback_data=f"{i + 2} {group_id} {group_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(
        text=f"Ingrese la cantidad de {pedigroup_product.name.lower()} que quisieras pedir:",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup)

    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quantity_group_id_and_name = query.data.split(" ")
    quantity = int(quantity_group_id_and_name[0])
    group_id = int(quantity_group_id_and_name[1])
    group_name = ' '.join(quantity_group_id_and_name[2:])
    product_id = context.user_data['product_id']
    restaurant_id = context.user_data['restaurant_id']
    pedigroup_product = Product.objects.get(id=product_id)
    user = query.from_user

    logger.info(f"{user.first_name} ({user.id}) {group_name} ({group_id}) added {quantity} {pedigroup_product.name}")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(ADD_PRODUCTS_BUTTON, callback_data=f"menu {restaurant_id} NO {group_id} {group_name}")],
        [InlineKeyboardButton(FINISH_INDIVIDUAL_ORDERS, callback_data="pedido finalizado")]
    ])

    await context.bot.edit_message_text(
        text=f"Agregué {quantity} {pedigroup_product.name.lower()} al pedido grupal de _{group_name}_!",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    register_user_and_add_to_group_if_required(user, group_id)
    current_user_orders.get(group_id).append(register_user_order(pedigroup_product, quantity, user))

    return ConversationHandler.END


async def start_command_misused(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: esto lo seguimos necesitando?
    await update.message.reply_text(
        "Este comando solo debe utilizarse luego de seleccionar la opcion _Contactar al bot_ desde un grupo",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: esto lo seguimos necesitando?
    await update.message.reply_text(
        "Bienvenido a PediGroup, para registrar un pedido individual debe iniciar "
        "uno grupal con el mensaje /iniciar_pedido"
    )
    return ConversationHandler.END


async def finalize_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    return ConversationHandler.END


async def load_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document or not update.message.reply_to_message:
        # Si no hay documento adjunto o no es una respuesta a nuestro mensaje inicial, ignoramos
        return

    # Verificar si el mensaje recibido es una respuesta al mensaje inicial
    if update.message.reply_to_message.text != CSV_INSTRUCTIONS_MESSAGE:
        # Si no es una respuesta al mensaje inicial, ignoramos
        return

    group_id = update.message.chat_id
    remote_file = await update.message.document.get_file()
    bytes_from_file = await remote_file.download_as_bytearray()
    try:
        restaurants, products, ommited_rows = create_entities_through_csv(bytes(bytes_from_file).decode(), group_id)
    except WrongHeadersForCsv:
        await update.message.reply_text(CSV_LOAD_EXCEPTION_MESSAGE)
        return
    except Exception as e:
        logger.exception(e)
        await update.message.reply_text(CSV_LOAD_UNKNOWN_EXCEPTION_MESSAGE)
        return

    await update.message.reply_text(CSV_SUCCESSFULLY_PROCESSED(restaurants, products, ommited_rows))


async def start_csv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text(ONLY_IN_GROUPS_MESSAGE)
        return
    group = update.message.chat
    user = update.message.from_user
    register_group_and_user_if_required(group, user)
    await update.message.reply_text(CSV_INSTRUCTIONS_MESSAGE)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: pensar si queremos mostrar dos help distintos para cuando estamos en grupos o chat individuales.
    await update.message.reply_text(HELP_MESSAGE)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(ALL_COMMANDS)


def start_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler(START_ORDER_COMMAND.command, start_order))
    application.add_handler(CallbackQueryHandler(finish_order, pattern=r'^Finalizar pedido\s+\S+'))
    application.add_handler(CommandHandler(LOAD_CSV_COMMAND.command, start_csv_upload))
    application.add_handler(MessageHandler(filters.Document.FileExtension("csv"), load_csv))
    application.add_handler(CommandHandler(HELP_COMMAND.command, show_help))

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_individual_order, filters=filters.Regex(r'^/start\s+\S+')),
                      CommandHandler("start", start_command_misused, filters=filters.Regex(r'^/start$')),
                      CallbackQueryHandler(show_initial_restaurants, pattern=r'^pedir(?:\s+(.*))?$'),
                      CallbackQueryHandler(show_initial_menu, pattern=r'^menu(?:\s+(.*))?$'),
                      CallbackQueryHandler(finalize_individual_order, pattern=r'^pedido finalizado$')],
        states={
            MENU: [CallbackQueryHandler(show_initial_menu, pattern=r'^menu(?:\s+(.*))?$'),
                   CallbackQueryHandler(show_restaurants, pattern=r'^Anterior(?:\s+(.*))?$'),
                   CallbackQueryHandler(show_restaurants, pattern=r'^Siguiente(?:\s+(.*))?$')],
            TYPE_SELECTION: [CallbackQueryHandler(handle_type_selection, pattern=r"^\d+.*"),
                             CallbackQueryHandler(show_menu, pattern=r'^Anterior(?:\s+(.*))?$'),
                             CallbackQueryHandler(show_menu, pattern=r'^Siguiente(?:\s+(.*))?$')],
            QUANTITY: [CallbackQueryHandler(handle_quantity)],
        },
        fallbacks=[],
    )

    application.add_handler(individual_order_handler)

    application.run_polling()
