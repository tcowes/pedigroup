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
order_started = False
# Variable global para ir almacenando los pedidos
current_user_orders: list[Order] = []

TYPE_SELECTION, QUANTITY = range(2)

def format_order(orders: list[Order]) -> str:
    grouped_order = defaultdict(lambda: 0)
    for order in orders:
        grouped_order[order.product.name] += order.quantity
    return "\n".join([f"{product_name}: {quantity}" for product_name, quantity in grouped_order.items()])


async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE, starting_order: bool):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un grupo.")
        return

    group = update.message.chat
    user = update.message.from_user
    group_id = update.message.chat_id
    context.user_data['group_id'] = group_id
    register_group_and_user_if_required(group, user)
    
    logger.info(f"{user.first_name} ({user.id}) called {'/iniciar_pedido' if starting_order else '/finalizar_pedido'}")

    global order_started
    global current_user_orders
    reply_markup = InlineKeyboardMarkup([])
    match starting_order, order_started:
        case True, False:
            message = (
                f"{user.first_name} inició un pedido!"
                "\n\nQuienes quieran pedir deben contactarse conmigo mediante un chat privado "
                "con el comando /pedido_individual."
            )
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Contactar bot", url=f"t.me/{context.bot.username}")]])
            order_started = True
        case True, True:
            message = "Ya hay un pedido en curso, finalizar con /finalizar_pedido"
        case False, True:
            register_group_order(group)
            formatted_order = format_order(current_user_orders)
            message = f"{user.first_name} finalizó el pedido!\n\nEn total se pidieron:\n{formatted_order}"
            current_user_orders = []
            order_started = False
        case False, False:
            message = "No hay ningún pedido en curso, iniciar uno nuevo con /iniciar_pedido"

    await context.bot.send_message(group_id, message, reply_markup=reply_markup)


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=True)


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=False)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_started
    if not order_started:
        await update.message.reply_text("Este comando solo puede llamarse una vez que alguien haya iniciado un pedido en un grupo con /iniciar_pedido.")
        return
    if update.message.chat.type != Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un chat privado.")
        return
    
    products = [prod for prod in Product.objects.all()]
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product.name, callback_data=product.id)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccioná que producto te gustaría pedir:", reply_markup=reply_markup)

    return TYPE_SELECTION


async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id = query.data
    await query.answer()

    context.user_data['product_id'] = product_id
    pedigroup_product = Product.objects.get(id=product_id)

    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([InlineKeyboardButton(i, callback_data=i), 
                         InlineKeyboardButton(i+1, callback_data=i+1),
                         InlineKeyboardButton(i+2, callback_data=i+2)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(text=f"Ingrese la cantidad de {pedigroup_product.name.lower()} que quisieras pedir:",
                                        chat_id=query.message.chat_id,
                                        message_id=query.message.message_id,
                                        reply_markup=reply_markup)

    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quantity = int(query.data)

    context.user_data['quantity'] = quantity
    product_id = context.user_data['product_id']
    pedigroup_product = Product.objects.get(id=product_id)
    user = query.from_user

    logger.info(f"{user.first_name} ({user.id}) added {quantity} {pedigroup_product.name}")
    await context.bot.edit_message_text(
        text=f"Agregué {quantity} {pedigroup_product.name.lower()} al pedido grupal!"
             "\n\nSi querés seguir agregando productos podes volver a pedir con /pedido_individual."
             "\nSi nadie mas quiere agregar productos, pueden finalizar el pedido desde el grupo con /finalizar_pedido.",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    group_id = context.user_data['group_id']
    register_user_and_add_to_group_if_required(user, group_id)
    current_user_orders.append(register_user_order(pedigroup_product, quantity, user))

    return ConversationHandler.END


async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido a PediGroup, para registrar un pedido debes usar el comando /pedido_individual.")
    return ConversationHandler.END


def start_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("iniciar_pedido", start_order))
    application.add_handler(CommandHandler("finalizar_pedido", finish_order))

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("pedido_individual", show_menu),
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
    for user_order in current_user_orders:
        group_order.add_order(user_order)
    return group_order