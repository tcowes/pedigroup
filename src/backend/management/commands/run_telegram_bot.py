from collections import defaultdict
from typing import Dict

from django.conf import settings
from backend.models import Group, Order, Product, User

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
# Variable global para ir almacenando el pedido
current_order: Dict[int, Dict[str, int]] = {}

TYPE_SELECTION, QUANTITY = range(2)

def format_order(total_order: dict) -> str:
    grouped_order = defaultdict(lambda: 0)
    for _, order in total_order.items():
        for item, quantity in order.items():
            grouped_order[item] += quantity
    return "\n".join([f"{item}: {quantity}" for item, quantity in grouped_order.items()])


async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE, starting_order: bool):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un grupo.")
        return

    group = update.message.chat
    user = update.message.from_user
    register_group_and_user_if_required(group, user)
    group_id = update.message.chat_id
    
    logger.info(f"{user.first_name} ({user.id}) called {'/iniciar_pedido' if starting_order else '/finalizar_pedido'}")

    global order_started
    global current_order
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
            formatted_order = format_order(current_order)
            message = f"{user.first_name} finalizó el pedido!\n\nEn total se pidieron:\n{formatted_order}"
            current_order = {}
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
    
    # Hacemos un select asíncrono... no es lo ideal, tenemos que investigar como poder hacer esto fuera del contexto.
    product_names = [prod for prod in Product.objects.all().values_list("name", flat=True)]
    keyboard = []
    for product_name in product_names:
        keyboard.append([InlineKeyboardButton(product_name, callback_data=product_name)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccioná que producto te gustaría pedir:", reply_markup=reply_markup)

    return TYPE_SELECTION


async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_name = query.data
    await query.answer()

    context.user_data['product_name'] = product_name

    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([InlineKeyboardButton(i, callback_data=i), 
                         InlineKeyboardButton(i+1, callback_data=i+1),
                         InlineKeyboardButton(i+2, callback_data=i+2)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(text=f"Ingrese la cantidad de {product_name.lower()} que quisieras pedir:",
                                        chat_id=query.message.chat_id,
                                        message_id=query.message.message_id,
                                        reply_markup=reply_markup)

    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quantity = int(query.data)

    context.user_data['quantity'] = quantity
    product_name = context.user_data['product_name']
    user = query.from_user

    if current_order.get(user.id) and current_order[user.id].get(product_name):
        current_order[user.id][product_name] += quantity
    elif current_order.get(user.id) and not current_order[user.id].get(product_name):
        current_order[user.id][product_name] = quantity
    else:
        current_order[user.id] = {product_name: quantity}

    logger.info(f"{user.first_name} ({user.id}) added {quantity} {product_name}")
    await context.bot.edit_message_text(
        text=f"Agregué {quantity} {product_name.lower()} al pedido grupal!"
             "\n\nSi querés seguir agregando productos podes volver a pedir con /pedido_individual."
             "\nSi nadie mas quiere agregar productos, pueden finalizar el pedido desde el grupo con /finalizar_pedido.",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    register_user_if_required(user)
    register_user_order(product_name, quantity, user)

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


def register_group_and_user_if_required(group, user):
    if not Group.objects.filter(id_app__contains=group.id).exists():
        Group.objects.create(name=group.title, id_app=group.id)
    register_user_if_required(user)


def register_user_if_required(user):
    if not User.objects.filter(id_app__contains=user.id).exists():
        User.objects.create(first_name=user.first_name, last_name=user.last_name, 
                            username=user.username, id_app=user.id)


def register_user_order(product_name, quantity, user):
    pedigroup_user = User.objects.get(id_app=user.id)
    pedigroup_product = Product.objects.get(name=product_name)
    pedigroup_user.place_order(pedigroup_product, quantity)