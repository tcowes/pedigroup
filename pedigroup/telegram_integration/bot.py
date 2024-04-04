from collections import defaultdict
from typing import Dict
import environ
env = environ.Env()
environ.Env.read_env()

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

BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Variable global para trackear el estado de un pedido.
order_started = False
# Variable global para ir almacenando el pedido
current_order: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(lambda: 0))

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

    user = update.message.from_user
    group_id = update.message.chat_id
    
    logger.debug(f"{user.first_name} ({user.id}) called {'/iniciar_pedido' if starting_order else '/finalizar_pedido'}")

    global order_started
    global current_order
    match starting_order, order_started:
        case True, False:
            message = (
                f"{user.first_name} inició un pedido de empanadas!"
                "\n\nQuienes quieran pedir deben contactarse conmigo mediante un chat privado "
                "con el comando /pedido_individual."
            )
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

    await context.bot.send_message(group_id, message)


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
    
    empanada_variety = ["Jamón y Queso", "Carne", "Verdura", "Pollo"]  # TODO: traer de la DB
    keyboard = []
    for empanada_type in empanada_variety:
        keyboard.append([InlineKeyboardButton(empanada_type, callback_data=empanada_type)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccioná que gusto de empanada te gustaría pedir:", reply_markup=reply_markup)

    return TYPE_SELECTION


async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    empanada_type = query.data
    await query.answer()

    context.user_data['empanada_type'] = empanada_type
    await query.message.reply_text(f"¿Cuantas empanadas de {empanada_type} quisieras pedir? Escribí solamente el número:")

    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity = int(update.message.text)

    context.user_data['quantity'] = quantity
    empanada_type = context.user_data['empanada_type']
    user = update.message.from_user

    await update.message.reply_text(
        f"Agregué {quantity} de {empanada_type} al pedido grupal!"
        "\n\nSi querés seguir agregando empanadas podes volver a pedir con /pedido_individual."
        "\nSi nadie mas quiere agregar pedidos, pueden finalizar el pedido desde el grupo con /finalizar_pedido."
    )

    logger.debug(f"{user.first_name} ({user.id}) added {quantity} {empanada_type}")
    current_order[user.id][empanada_type] += quantity

    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("iniciar_pedido", start_order))
    application.add_handler(CommandHandler("finalizar_pedido", finish_order))

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("pedido_individual", show_menu)],
        states={
            TYPE_SELECTION: [CallbackQueryHandler(handle_type_selection)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
        },
        fallbacks=[],
    )

    application.add_handler(individual_order_handler)

    application.run_polling()
