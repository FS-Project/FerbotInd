# Ferbot, this is a bot for management your group
# This source code copy from UserIndoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2021 FS Project <https://github.com/FS-Project/Ferbot.git>
# 
# UserindoBot
# Copyright (C) 2020  UserindoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO
from time import sleep

from telegram import TelegramError
from telegram.error import BadRequest, TimedOut, Unauthorized
from telegram.ext import CommandHandler, Filters, MessageHandler

from ferbot.modules.no_sql import users_db
from ferbot import LOGGER, OWNER_ID, dispatcher
from ferbot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4
CHAT_GROUP = 10


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = users_db.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0]["_id"]

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj["_id"])
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == "Chat not found":
                    pass
                else:
                    LOGGER.exception("Error extracting user ID")

    return None


def broadcast(update, context):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats = users_db.get_all_chats() or []
        failed = 0
        for chat in chats:
            try:
                context.bot.sendMessage(int(chat["chat_id"]), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning(
                    "Couldn't send broadcast to %s, group name %s",
                    str(chat["chat_id"]),
                    str(chat["chat_name"]),
                )

        update.effective_message.reply_text(
            "Broadcast complete. {} groups failed to receive the message, probably "
            "due to being kicked.".format(failed)
        )


def log_user(update, context):
    chat = update.effective_chat
    msg = update.effective_message

    users_db.update_user(
        msg.from_user.id, msg.from_user.username, chat.id, chat.title
    )

    if msg.reply_to_message:
        users_db.update_user(
            msg.reply_to_message.from_user.id,
            msg.reply_to_message.from_user.username,
            chat.id,
            chat.title,
        )

    if msg.forward_from:
        users_db.update_user(msg.forward_from.id, msg.forward_from.username)


def chats(update, context):
    all_chats = users_db.get_all_chats() or []
    chatfile = "List of chats.\n"
    for chat in all_chats:
        chatfile += "{} - ({})\n".format(chat["chat_name"], chat["chat_id"])

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="chatlist.txt",
            caption="Here is the list of chats in my database.",
        )


def chat_checker(update, context):
    try:
        if (
            update.effective_message.chat.get_member(
                context.bot.id
            ).can_send_messages
            is False
        ):
            context.bot.leaveChat(update.effective_message.chat.id)
    except (TimedOut, Unauthorized, BadRequest):
        pass


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """I've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me."""
    num_chats = users_db.get_user_num_chats(user_id)
    return """I've seen them in <code>{}</code> chats in total.""".format(
        num_chats
    )


def __stats__():
    return "× {} users, across {} chats".format(
        users_db.num_users(), users_db.num_chats()
    )


def __migrate__(old_chat_id, new_chat_id):
    users_db.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler(
    "broadcast", broadcast, filters=Filters.user(OWNER_ID), run_async=True
)
USER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, log_user, run_async=True
)
CHATLIST_HANDLER = CommandHandler(
    "chatlist", chats, filters=CustomFilters.sudo_filter, run_async=True
)
CHAT_CHECKER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, chat_checker, run_async=True
)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)
