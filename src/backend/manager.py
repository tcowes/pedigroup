from dataclasses import dataclass
from typing import Dict, Tuple, List

from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes


@dataclass
class MessageWithMarkup:
    message: str
    markup: InlineKeyboardMarkup


class GroupOrderManager:
    def __init__(self):
        self._groups: Dict[int, Tuple[List, int]] = dict()
        self._message_references: Dict[int, MessageWithMarkup] = dict()

    def add_group(self, group_id, message_id, message_with_markup):
        self._groups[group_id] = ([], message_id)
        self._message_references[group_id] = message_with_markup

    def remove_group(self, group_id):
        self._groups.pop(group_id)
        self._message_references.pop(group_id)

    def has_on_going_orders(self, group_id) -> bool:
        return len(self._groups.get(group_id, [[]])[0]) > 0

    async def add_currently_ordering_user(self, user_id, user_name, group_id, context: ContextTypes.DEFAULT_TYPE):
        self._groups[group_id][0].append((user_id, user_name))
        message_reference = self._message_references[group_id]
        new_message = message_reference.message + f"\n\n{user_name} está haciendo su pedido... 🔁"
        self._message_references[group_id].message = new_message
        message_id = self._groups[group_id][1]
        await context.bot.edit_message_text(new_message, group_id, message_id, reply_markup=message_reference.markup)

    async def remove_currently_ordering_user(self, user_id, group_id, context: ContextTypes.DEFAULT_TYPE):
        if group_id not in self._groups:
            return

        user_name_that_finished = None
        ordering_users, message_id = self._groups[group_id]
        for users in self._groups[group_id][0]:
            if users[0] == user_id:
                user_name_that_finished = users[1]
        self._groups[group_id] = ([(u_id, user_name) for u_id, user_name in ordering_users if u_id != user_id], message_id)

        message_reference = self._message_references[group_id]
        new_message = message_reference.message.replace(
            f"{user_name_that_finished} está haciendo su pedido... 🔁",
            f"{user_name_that_finished} finalizó su pedido ✅"
        )
        self._message_references[group_id].message = new_message
        message_id = self._groups[group_id][1]
        await context.bot.edit_message_text(new_message, group_id, message_id, reply_markup=message_reference.markup)