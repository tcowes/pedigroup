from typing import Dict

from django.conf import settings

from backend.constants import *
from backend.exceptions import WrongHeadersForCsv
from backend.manager import GroupOrderManager, MessageWithMarkup
from backend.models import Order, Product

import logging
from telegram import CallbackQuery, Chat, InlineKeyboardButton, InlineKeyboardMarkup, MaybeInaccessibleMessage, Update
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
    register_group_order, get_last_five_orders_from_group_as_string, get_user_groups,
    get_last_five_orders_from_user_in_group_as_string, get_group, get_paginated_products_by_restaurant, get_product,
    count_restaurants_for_group, get_restaurant, get_paginated_restaurants_by_group
)
from django.core.management.base import BaseCommand

from backend.utils import format_individual_orders, format_order

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
# Variable global para ir almacenando los pedidos individuales de cada grupo diferenciados por usuario
current_user_orders: Dict[int, Dict[int, list[Order]]] = {}
# Variable global para almacenar los mensajes de los pedidos individuales que se pueden editar actualmente
editable_user_order_messages: Dict[int, list[MaybeInaccessibleMessage]] = {}

MENU, TYPE_SELECTION, QUANTITY, MODIFY = range(4)
GROUP_SELECTION_FOR_RECORD = 0


manager = GroupOrderManager()


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
        current_user_orders[group_id] = {}
    reply_markup = InlineKeyboardMarkup([])
    recently_initiated = False
    match orders_initiated.get(group_id):
        case False:
            message = f"{user.first_name}" + USER_STARTED_ORDER_MESSAGE
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contactar bot", url=f"t.me/{context.bot.username}?start={group_id}")],
                 [InlineKeyboardButton("Finalizar pedido", callback_data=f"Finalizar pedido {group_id}")]])
            orders_initiated[group_id] = True
            recently_initiated = True
        case True:
            message = IN_COURSE_ORDER_MESSAGE

    sent_message = await context.bot.send_message(group_id, message, reply_markup=reply_markup, parse_mode="Markdown")
    if recently_initiated:
        manager.add_group(group_id, sent_message.message_id, MessageWithMarkup(message, reply_markup))


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orders_initiated
    global current_user_orders

    query = update.callback_query
    group_id = int(query.data.removeprefix("Finalizar pedido "))
    user = query.from_user
    register_user_and_add_to_group_if_required(user, group_id)

    if manager.has_on_going_orders(group_id):
        await context.bot.send_message(group_id, THERE_ARE_ON_GOING_ORDERS_MESSAGE)
        return

    logger.info(f"{user.first_name} ({user.id}) (group_id: {group_id}) finished the current order")
    group_order = [order for individual_orders in current_user_orders[group_id].values() for order in individual_orders]
    current_user_orders[group_id] = {}
    orders_initiated[group_id] = False

    if len(group_order) > 0:
        pedigroup_group_order = register_group_order(group_id, group_order)
        formatted_order, total_quantity = format_order(group_order)
        await context.bot.send_message(
            group_id,
            f"{user.first_name} finalizó el pedido!\n\nEn total se pidieron:\n{formatted_order}\n\n"
            f"Cantidad total de productos: {total_quantity}\n\n"
            f"Precio estimado: ${pedigroup_group_order.estimated_price}",
        )
    else:
        await context.bot.send_message(
            group_id,
            f"{user.first_name} finalizó el pedido, pero el mismo no fue registrado ya que no se "
            "realizaron pedidos individuales.",
        )
    manager.remove_group(group_id)
    await query.delete_message()


async def start_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_with_group_id = update.message.text
    group_id = int(message_with_group_id.removeprefix("/start "))
    pedigroup_group = get_group(group_id)
    user = update.message.from_user
    group_name = pedigroup_group.name
    if not current_user_orders.get(group_id).get(user.id):
        current_user_orders[group_id][user.id] = []
    await manager.add_currently_ordering_user(user.id, user.first_name, group_id, context)
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Realizar pedido individual", callback_data=f"pedir YES|{group_id}|{group_name}")]])
    await update.message.reply_text(f"Bienvenido a PediGroup, queres añadir pedidos individuales para _{group_name}_?",
                                    reply_markup=reply_markup, parse_mode="Markdown")


async def show_initial_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    if_first_message, group_id, group_name = query.data.removeprefix("pedir ").split("|")
    group_id = int(group_id)
    global orders_initiated
    if not orders_initiated[group_id]:
        await update.message.reply_text(NO_ORDER_INITIATED_MESSAGE)
        return

    restaurants_count = count_restaurants_for_group(group_id)
    context.user_data['current_page'] = 0
    context.user_data['quantity_of_items'] = restaurants_count

    if restaurants_count > 0:
        reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, "Restaurants", False)
        await message_of_restaurants_according_to_flag(context, query, if_first_message, reply_markup)
    else:
        await query.message.reply_text(NO_RESTAURANTS_FOUND_MESSAGE)
        return ConversationHandler.END
    return MENU


async def message_of_restaurants_according_to_flag(context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, 
                                                   if_first_message, reply_markup):
    if if_first_message == "YES":
        await query.message.reply_text(PICK_RESTAURANTS_MESSAGE, reply_markup=reply_markup)
    else:
        await context.bot.edit_message_text(PICK_RESTAURANTS_MESSAGE,
                                                chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                reply_markup=reply_markup)


async def show_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reply_markup = select_page_to_show(update, context, "Restaurants", False)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return MENU


async def show_initial_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    restaurant_id, if_first_message, group_id, group_name = query.data.removeprefix("menu ").split("|")
    restaurant = get_restaurant(restaurant_id)

    context.user_data['restaurant_id'] = restaurant_id
    context.user_data['current_page'] = 0
    context.user_data['quantity_of_items'] = restaurant.products_quantity()
    reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, "Products", False)

    if if_first_message == "YES":
        await query.message.reply_text(PICK_PRODUCTS_MESSAGE, reply_markup=reply_markup)
    else:
        await message_to_select_product(context, query, reply_markup)

    return TYPE_SELECTION


async def message_to_select_product(context: ContextTypes.DEFAULT_TYPE, 
                                    query: CallbackQuery, reply_markup):
    await context.bot.edit_message_text(PICK_PRODUCTS_MESSAGE,
                                        chat_id=query.message.chat_id,
                                        message_id=query.message.message_id,
                                        reply_markup=reply_markup)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reply_markup = select_page_to_show(update, context, "Products", False)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return TYPE_SELECTION


def select_page_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE, items_to_paginate, modifier_mode):
    query = update.callback_query
    page_movement, group_id, group_name = query.data.split("|")
    page = context.user_data['current_page']

    if page_movement == "Siguiente":
        context.user_data['current_page'] = page + 1
    else:
        context.user_data['current_page'] = page - 1

    reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, items_to_paginate, modifier_mode)
    return reply_markup


def show_menu_or_restaurant_page(context: ContextTypes.DEFAULT_TYPE, group_id: int, 
                                 group_name, items_to_show, modifier_mode: bool):
    page = context.user_data['current_page']
    quantity_of_items = context.user_data['quantity_of_items']
    first_item = page * 5
    last_item = first_item + 5
    keyboard = []

    if items_to_show == "Restaurants":
        restaurants = [rest for rest in get_paginated_restaurants_by_group(group_id, first_item, last_item)]
        for restaurant in restaurants:
            keyboard.append([InlineKeyboardButton(restaurant.name,
                                                  callback_data=f"menu {restaurant.id}|NO|{group_id}|{group_name}")])
    elif items_to_show == "Products":
        restaurant_id = context.user_data['restaurant_id']
        products = [prod for prod in get_paginated_products_by_restaurant(restaurant_id, first_item, last_item)]
        for product in products:
            keyboard.append([InlineKeyboardButton(product.name,
                                                  callback_data=f"{product.id}|{restaurant_id}|{group_id}|{group_name}")])

    previous_button = InlineKeyboardButton(PREVIOUS_BUTTON, callback_data=f"Anterior|{group_id}|{group_name}")
    next_button = InlineKeyboardButton(NEXT_BUTTON, callback_data=f"Siguiente|{group_id}|{group_name}")

    if page == 0 and quantity_of_items > last_item:
        keyboard.append([next_button])
    elif page > 0 and quantity_of_items > last_item:
        keyboard.append([previous_button, next_button])
    elif page > 0 and quantity_of_items <= last_item:
        keyboard.append([previous_button])

    if (not modifier_mode) & (items_to_show == "Products"):
        keyboard.append(
            [InlineKeyboardButton(BACK_TO_RESTAURANTS_BUTTON, callback_data=f"pedir NO|{group_id}|{group_name}")])

    return InlineKeyboardMarkup(keyboard)


async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id, restaurant_id, group_id, group_name = query.data.split("|")
    pedigroup_product = get_product(product_id)

    context.user_data['product_id'] = product_id

    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([InlineKeyboardButton(i, callback_data=f"{i}|{group_id}|{group_name}"),
                         InlineKeyboardButton(i + 1, callback_data=f"{i + 1}|{group_id}|{group_name}"),
                         InlineKeyboardButton(i + 2, callback_data=f"{i + 2}|{group_id}|{group_name}")])
    keyboard.append([InlineKeyboardButton(BACK_TO_PRODUCTS_BUTTON,
                                          callback_data=f"menu {restaurant_id}|NO|{group_id}|{group_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_to_select_quantity(context, query, pedigroup_product, reply_markup)

    return QUANTITY


async def message_to_select_quantity(context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, 
                                  pedigroup_product: Product, reply_markup):
    await context.bot.edit_message_text(
        text=PICK_QUANTITY_MESSAGE(pedigroup_product.name.lower()),
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup)


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quantity, group_id, group_name = query.data.split("|")
    quantity = int(quantity)
    group_id = int(group_id)
    product_id = context.user_data['product_id']
    restaurant_id = context.user_data['restaurant_id']
    pedigroup_product = get_product(product_id)
    user = query.from_user

    logger.info(f"{user.first_name} ({user.id}) {group_name} ({group_id}) added {quantity} {pedigroup_product.name}")

    register_user_and_add_to_group_if_required(user, group_id)
    pedigroup_order = register_user_order(pedigroup_product, quantity, user)

    reply_markup = show_modify_buttons(quantity, group_id, group_name, restaurant_id, 
                                       pedigroup_product, pedigroup_order)

    await individual_order_message_finalized(context, query, quantity, group_name, 
                                             pedigroup_product, reply_markup)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(ADD_PRODUCTS_BUTTON, callback_data=f"menu {restaurant_id}|NO|{group_id}|{group_name}")],
        [InlineKeyboardButton(FINISH_INDIVIDUAL_ORDERS, callback_data=f"pedido finalizado {group_id}|{group_name}")]
    ])

    await query.message.reply_text(
        text=CONTINUE_ADDING_ORDERS_MESSAGE,
        reply_markup=reply_markup
    )

    current_user_orders.get(group_id).get(user.id).append(pedigroup_order)

    if not editable_user_order_messages.get(user.id):
        editable_user_order_messages[user.id] = []
    editable_user_order_messages.get(user.id).append(query.message)

    return ConversationHandler.END


async def show_initial_modify_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    restaurant_id, order_id, quantity, group_id, group_name = query.data.removeprefix("modificar producto ").split("|")
    restaurant = get_restaurant(restaurant_id)
    order_id = int(order_id)

    context.user_data['restaurant_id'] = restaurant_id
    context.user_data['order_id'] = order_id
    context.user_data['quantity'] = quantity
    context.user_data['current_page'] = 0
    context.user_data['quantity_of_items'] = restaurant.products_quantity()
    reply_markup = show_menu_or_restaurant_page(context, group_id, group_name, "Products", True)

    await message_to_select_product(context, query, reply_markup)

    return MODIFY


async def show_modify_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reply_markup = select_page_to_show(update, context, "Products", True)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

    return MODIFY


async def finish_modify_product_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id, restaurant_id, group_id, group_name = query.data.split("|")
    quantity = context.user_data['quantity']
    order_id = context.user_data['order_id']
    group_id = int(group_id)
    pedigroup_product = get_product(product_id)
    user = query.from_user

    logger.info(
        f"{user.first_name} ({user.id}) {group_name} ({group_id}) modify his order ({order_id}) with {quantity} {pedigroup_product.name}")

    pedigroup_order = modify_pedigroup_order("product", pedigroup_product, group_id, order_id, user.id)

    reply_markup = show_modify_buttons(quantity, group_id, group_name, restaurant_id, 
                                       pedigroup_product, pedigroup_order)

    await individual_order_message_finalized(context, query, quantity, group_name, 
                                             pedigroup_product, reply_markup)

    return ConversationHandler.END


async def show_modify_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    restaurant_id, order_id, product_id, group_id, group_name = query.data.removeprefix("modificar cantidad ").split("|")
    pedigroup_product = get_product(product_id)
    order_id = int(order_id)

    context.user_data['restaurant_id'] = restaurant_id
    context.user_data['order_id'] = order_id
    context.user_data['product_id'] = product_id

    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([InlineKeyboardButton(i, callback_data=f"modificado {i}|{group_id}|{group_name}"),
                         InlineKeyboardButton(i + 1, callback_data=f"modificado {i + 1}|{group_id}|{group_name}"),
                         InlineKeyboardButton(i + 2, callback_data=f"modificado {i + 2}|{group_id}|{group_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_to_select_quantity(context, query, pedigroup_product, reply_markup)

    return MODIFY


async def finish_modify_quantity_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quantity, group_id, group_name = query.data.removeprefix("modificado ").split("|")
    quantity = int(quantity)
    group_id = int(group_id)
    restaurant_id = context.user_data['restaurant_id']
    order_id = context.user_data['order_id']
    product_id = context.user_data['product_id']
    pedigroup_product = get_product(product_id)
    user = query.from_user

    logger.info(
        f"{user.first_name} ({user.id}) {group_name} ({group_id}) modify his order ({order_id}) with {quantity} {pedigroup_product.name}")

    pedigroup_order = modify_pedigroup_order("quantity", quantity, group_id, order_id, user.id)

    reply_markup = show_modify_buttons(quantity, group_id, group_name, restaurant_id, 
                                       pedigroup_product, pedigroup_order)

    await individual_order_message_finalized(context, query, quantity, group_name, 
                                             pedigroup_product, reply_markup)

    return ConversationHandler.END


def modify_pedigroup_order(data_to_be_modified, data, group_id: int, order_id: int, user_id: int):
    pedigroup_order = next((order for order in current_user_orders.get(group_id).get(user_id) if order.id == order_id), None)
    if data_to_be_modified == "product":
        pedigroup_order.modify_product(data)
    elif data_to_be_modified == "quantity":
        pedigroup_order.modify_quantity(data)
    current_user_orders[group_id][user_id] = [order for order in current_user_orders.get(group_id).get(user_id) if order.id != order_id]
    current_user_orders.get(group_id).get(user_id).append(pedigroup_order)
    return pedigroup_order


def show_modify_buttons(quantity, group_id, group_name, restaurant_id, pedigroup_product, pedigroup_order):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(MODIFY_PRODUCT_BUTTON,
                              callback_data=f"modificar producto {restaurant_id}|{pedigroup_order.id}|{quantity}|{group_id}|{group_name}"),
         InlineKeyboardButton(MODIFY_QUANTITY_BUTTON,
                              callback_data=f"modificar cantidad {restaurant_id}|{pedigroup_order.id}|{pedigroup_product.id}|{group_id}|{group_name}")]
    ])
    
    return reply_markup


async def individual_order_message_finalized(context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, 
                                             quantity, group_name, pedigroup_product: Product, reply_markup):
    await context.bot.edit_message_text(
        text=f"Agregué {quantity} {pedigroup_product.name.lower()} al pedido grupal de _{group_name}_!",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def start_command_misused(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        DO_NOT_USE_IT_LIKE_THIS_MESSAGE,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_members = update.message.new_chat_members
    bot_id = context.bot.id
    for member in new_members:
        if member.id == bot_id:
            group_id = update.message.chat_id
            await context.bot.send_message(group_id, "Bienvenidos a PediGroup!\n\n" + HELP_MESSAGE)
    return ConversationHandler.END


async def finalize_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_user_orders
    
    query = update.callback_query
    user = query.from_user
    group_id, group_name = query.data.removeprefix("pedido finalizado ").split("|")
    group_id = int(group_id)

    await manager.remove_currently_ordering_user(user.id, int(group_id), context)
    for message in editable_user_order_messages.get(user.id):
        await context.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    editable_user_order_messages[user.id] = []

    individual_orders = current_user_orders[group_id][user.id]

    if len(individual_orders) > 0:
        formatted_order, total_quantity, estimated_price = format_individual_orders(individual_orders)
        await context.bot.edit_message_text(
            text=f"Finalizaste tus pedidos individuales para _{group_name}_!\n\nPediste:\n{formatted_order}\n\n"
                 f"Cantidad total de productos: {total_quantity}\n\n"
                 f"Precio estimado: ${estimated_price}\n\n"
                 "Para finalizar el pedido grupal debes hacerlo desde el chat del grupo.",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=None,
            parse_mode="Markdown"
        )
    else:
        await context.bot.edit_message_text(
            text=INDIVIDUAL_ORDERS_COMPLETED_MESSAGE(group_name),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=None,
            parse_mode="Markdown"
        )
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


async def show_order_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.chat.type == Chat.PRIVATE:
        user_groups = get_user_groups(user.id)
        if not user_groups:
            await update.message.reply_text(USER_NOT_IN_GROUPS_YET_MESSAGE)
            return ConversationHandler.END
        buttons = [
            [InlineKeyboardButton(group.name, callback_data=f"{group.id_app}|{user.id}|{group.name}")]
            for group in user_groups
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "Selecciona un grupo del que quieras ver tus últimos pedidos:",
            reply_markup=reply_markup
        )
        return GROUP_SELECTION_FOR_RECORD
    else:
        group = update.message.chat
        register_group_and_user_if_required(group, user)
        await update.message.reply_text(get_last_five_orders_from_group_as_string(group.id))
        return ConversationHandler.END


async def select_user_group_for_orders_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    group_id, user_id, group_name = query.data.split("|")
    message = (
        f"Mostrando los últimos 5 pedidos realizados desde el grupo _{group_name}_\n\n"
        f"{get_last_five_orders_from_user_in_group_as_string(user_id, group_id)}"
    )
    await context.bot.edit_message_text(
        text=message,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=None,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


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
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start_message))

    orders_record_handler = ConversationHandler(
        entry_points=[CommandHandler(SHOW_ORDER_RECORD_COMMAND.command, show_order_record)],
        states={
            GROUP_SELECTION_FOR_RECORD: [CallbackQueryHandler(select_user_group_for_orders_record)]
        },
        fallbacks=[],
    )

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_individual_order, filters=filters.Regex(r'^/start\s+\S+')),
                      CommandHandler("start", start_command_misused, filters=filters.Regex(r'^/start$')),
                      CallbackQueryHandler(show_initial_restaurants, pattern=r'^pedir(?:\s+(.*))?$'),
                      CallbackQueryHandler(show_initial_menu, pattern=r'^menu(?:\s+(.*))?$'),
                      CallbackQueryHandler(show_initial_modify_product, pattern=r'^modificar producto(?:\s+(.*))?$'),
                      CallbackQueryHandler(show_modify_quantity, pattern=r'^modificar cantidad(?:\s+(.*))?$'),
                      CallbackQueryHandler(finalize_individual_order, pattern=r'^pedido finalizado(?:\s+(.*))?$')],
        states={
            MENU: [CallbackQueryHandler(show_initial_menu, pattern=r'^menu(?:\s+(.*))?$'),
                   CallbackQueryHandler(show_restaurants)],
            TYPE_SELECTION: [CallbackQueryHandler(handle_type_selection, pattern=r"^\d+.*"),
                             CallbackQueryHandler(show_initial_restaurants, pattern=r'^pedir(?:\s+(.*))?$'),
                             CallbackQueryHandler(show_menu)],
            QUANTITY: [CallbackQueryHandler(show_initial_menu, pattern=r'^menu(?:\s+(.*))?$'),
                       CallbackQueryHandler(handle_quantity)],
            MODIFY: [CallbackQueryHandler(finish_modify_quantity_order, pattern=r'^modificado(?:\s+(.*))?$'),
                     CallbackQueryHandler(finish_modify_product_order, pattern=r"^\d+.*"),
                     CallbackQueryHandler(show_modify_product)]
        },
        fallbacks=[],
    )

    application.add_handler(individual_order_handler)
    application.add_handler(orders_record_handler)

    application.run_polling()
