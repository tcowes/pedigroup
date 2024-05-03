from collections import defaultdict
from typing import Dict

from django.conf import settings
from backend.models import Group, GroupOrder, Order, Product, User

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
)

from django.core.management.base import BaseCommand

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start telegram bot"

    def handle(self, *args, **options):
        start_bot()

# Variable global para trackear el estado de un pedido.
orders_initiated: Dict[int, bool] = {}
# Variable global para ir almacenando los pedidos
current_user_orders: Dict[int, list[Order]] = {}

TYPE_SELECTION, QUANTITY = range(2)

def format_order(orders: list[Order]) -> str:
    grouped_order = defaultdict(lambda: 0)
    for order in orders:
        grouped_order[order.product_name()] += order.quantity
    return "\n".join([f"{product_name}: {quantity}" for product_name, quantity in grouped_order.items()])


async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE, starting_order: bool):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un grupo.")
        return

    group = update.message.chat
    user = update.message.from_user
    group_id = update.message.chat_id
    register_group_and_user_if_required(group, user)
    
    logger.info(f"{user.first_name} ({user.id}) {group.title} ({group_id}) called {'/iniciar_pedido' if starting_order else '/finalizar_pedido'}")

    global orders_initiated
    global current_user_orders
    if not orders_initiated.get(group_id):
        orders_initiated[group_id] = False
        current_user_orders[group_id] = []
    reply_markup = InlineKeyboardMarkup([])
    match starting_order, orders_initiated.get(group_id):
        case True, False:
            message = (
                f"{user.first_name} inició un pedido!"
                "\n\nQuienes quieran pedir deben contactarse conmigo mediante un chat privado "
                "clickeando el siguiente boton ↓"
            )
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Contactar bot", url=f"t.me/{context.bot.username}?start={group_id}")]])
            orders_initiated[group_id] = True
        case True, True:
            message = "Ya hay un pedido en curso, finalizar con /finalizar_pedido"
        case False, True:
            register_group_order(group)
            formatted_order = format_order(current_user_orders.get(group_id))
            message = f"{user.first_name} finalizó el pedido!\n\nEn total se pidieron:\n{formatted_order}"
            current_user_orders[group_id] = []
            orders_initiated[group_id] = False
        case False, False:
            message = "No hay ningún pedido en curso, iniciar uno nuevo con /iniciar_pedido"

    await context.bot.send_message(group_id, message, reply_markup=reply_markup)


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=True)


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=False)


async def start_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_with_group_id = update.message.text
    group_id = int(message_with_group_id.removeprefix("/start "))
    pedigroup_group = Group.objects.get(id_app=group_id)
    group_name = pedigroup_group.name
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Realizar pedido individual", callback_data=f"pedir {group_id} {group_name}")]])
    await update.message.reply_text(f"Bienvenido a PediGroup, queres añadir pedidos individuales para _{group_name}_?", reply_markup=reply_markup, parse_mode="Markdown")


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    message_with_group_id_and_name = query.data.removeprefix("pedir ")
    message_with_group_id_and_name = message_with_group_id_and_name.split(" ")
    group_id = int(message_with_group_id_and_name[0])
    group_name = ' '.join(message_with_group_id_and_name[1:])
    global orders_initiated
    if not orders_initiated[group_id]:
        await update.message.reply_text("Este comando solo puede llamarse una vez que alguien haya iniciado un pedido en un grupo con /iniciar_pedido.")
        return
    
    products = [prod for prod in Product.objects.all()]
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product.name, callback_data=f"{product.id} {group_id} {group_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Seleccioná que producto te gustaría pedir:", reply_markup=reply_markup)

    return TYPE_SELECTION


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
                         InlineKeyboardButton(i+1, callback_data=f"{i+1} {group_id} {group_name}"),
                         InlineKeyboardButton(i+2, callback_data=f"{i+2} {group_id} {group_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(text=f"Ingrese la cantidad de {pedigroup_product.name.lower()} que quisieras pedir:",
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
    pedigroup_product = Product.objects.get(id=product_id)
    user = query.from_user

    logger.info(f"{user.first_name} ({user.id}) {group_name} ({group_id}) added {quantity} {pedigroup_product.name}")

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"Añadir mas pedidos", callback_data=f"pedir {group_id} {group_name}")],
                                         [InlineKeyboardButton(f"Finalizar pedidos individuales", callback_data="pedido finalizado")]])

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


async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido a PediGroup, para registrar un pedido individual debe iniciar uno grupal con el mensaje /iniciar_pedido")
    return ConversationHandler.END


async def finalize_individual_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    return ConversationHandler.END


def start_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("iniciar_pedido", start_order))
    application.add_handler(CommandHandler("finalizar_pedido", finish_order))

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("pedido_individual", show_menu),
                      CommandHandler("start", start_individual_order),
                      CallbackQueryHandler(show_menu, pattern=r'^pedir(?:\s+(.*))?$'),
                      CallbackQueryHandler(finalize_individual_order, pattern=r'^pedido finalizado$'),
                      MessageHandler(filters.ALL, start_message)],
        states={
            TYPE_SELECTION: [CallbackQueryHandler(handle_type_selection)],
            QUANTITY: [CallbackQueryHandler(handle_quantity)],
        },
        fallbacks=[],
    )

    application.add_handler(individual_order_handler)

    application.run_polling()


def register_group_and_user_if_required(group, userApp):
    if not Group.objects.filter(id_app__contains=group.id).exists():
        Group.objects.create(name=group.title, id_app=group.id)
    register_user_and_add_to_group_if_required(userApp, group.id)


def register_user_and_add_to_group_if_required(userApp, group_id):
    if not User.objects.filter(id_app__contains=userApp.id).exists():
        user = User.objects.create(first_name=userApp.first_name, last_name=userApp.last_name, 
                                   username=userApp.username, id_app=userApp.id, is_bot=userApp.is_bot)
        group = Group.objects.get(id_app=group_id)
        group.add_user(user)


def register_user_order(product, quantity, user):
    pedigroup_user = User.objects.get(id_app=user.id)
    return pedigroup_user.place_order(product, quantity)


def register_group_order(group):
    pedigroup_group = Group.objects.get(id_app=group.id)
    group_order = GroupOrder.objects.create(group=pedigroup_group)
    for user_order in current_user_orders.get(group.id):
        group_order.add_order(user_order)
    return group_order