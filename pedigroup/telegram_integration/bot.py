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


async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE, starting_order: bool):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un grupo.")
        return

    user = update.message.from_user
    group_id = update.message.chat_id
    
    global order_started
    global current_order
    match starting_order, order_started:
        case True, False:
            message = f"{user.first_name} inició un pedido de empanadas, quienes quieran pedir deben enviar su pedido."
            order_started = True
        case True, True:
            message = "Ya hay un pedido en curso, finalizar con /finalizar_pedido"
        case False, True:
            # TODO: formatear correctamente el current_order
            message = f"{user.first_name} finalizó el pedido! {current_order}"
            current_order = {}
            order_started = False
        case False, False:
            message = "No hay ningún pedido en curso, iniciar uno nuevo con /iniciar_pedido"

    await context.bot.send_message(group_id, message)


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=True)


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_order(update, context, starting_order=False)


async def show_empanada_variety(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: falta handleo de si está o no el pedido inciado
    if update.message.chat.type != Chat.PRIVATE:
        await update.message.reply_text("Este comando solo puede llamarse desde un chat privado.")
        return
    
    empanada_variety = ["Jamón y Queso", "Carne", "Verdura"]  # TODO: traer de la DB
    keyboard = []
    for empanada_type in empanada_variety:
        keyboard.append([InlineKeyboardButton(empanada_type, callback_data=empanada_type)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona qué gusto de empanada te gustaría pedir:", reply_markup=reply_markup)

    return TYPE_SELECTION


async def handle_empanada_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: falta handleo de si está o no el pedido inciado
    query = update.callback_query
    empanada_type = query.data
    await query.answer()

    context.user_data['empanada_type'] = empanada_type
    await query.message.reply_text(f"Seleccionaste {empanada_type}. ¿Cuantas quisieras pedir?")

    return QUANTITY


async def handle_empanada_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: falta handleo de si está o no el pedido inciado
    # TODO: asegurar que nos manden un int.
    quantity = int(update.message.text)

    context.user_data['quantity'] = quantity
    empanada_type = context.user_data['empanada_type']
    await update.message.reply_text(f"Has seleccionado {quantity} empanadas de tipo {empanada_type}.")

    current_order[update.message.from_user.id][empanada_type] += quantity

    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("iniciar_pedido", start_order))
    application.add_handler(CommandHandler("finalizar_pedido", finish_order))

    individual_order_handler = ConversationHandler(
        entry_points=[CommandHandler("empanadas", show_empanada_variety)],
        states={
            TYPE_SELECTION: [CallbackQueryHandler(handle_empanada_selection)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_empanada_quantity)],
        },
        fallbacks=[],
    )

    application.add_handler(individual_order_handler)


    application.run_polling()