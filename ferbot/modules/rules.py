# Ferbot, this is a bot for management your group
# This source code copy from UserIndoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2021 FS Project <https://github.com/FS-Project/FerbotInd.git>
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

from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import escape_markdown

from ferbot import dispatcher
from ferbot.modules.no_sql import get_collection
from ferbot.modules.helper_funcs.alternate import typing_action
from ferbot.modules.helper_funcs.chat_status import user_admin
from ferbot.modules.helper_funcs.string_handling import markdown_parser


RULES_DATA = get_collection("RULES")


@typing_action
def get_rules(update, context):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "Pintasan rules untuk obrolan ini belum disetel dengan benar! "
                "Minta admin untuk memperbaikinya.",
            )
            return
        else:
            raise

    rules = chat_rules(chat_id)
    text = "Rules untuk *{}* adalah:\n\n{}".format(
        escape_markdown(chat.title), rules
    )

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(
            user.id,
            "Admin grup belum menetapkan rules apa pun untuk obrolan ini.. "
            "Bukan berarti obrolan ini melanggar hukum...!",
        )
    elif rules:
        update.effective_message.reply_text(
            "Hubungi saya di PM untuk mendapatkan rules grup ini.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Rules Grup",
                            url="t.me/{}?start={}".format(
                                bot.username, chat_id
                            ),
                        )
                    ]
                ]
            ),
        )
    else:
        update.effective_message.reply_text(
            "Admin grup belum menetapkan rules apa pun untuk obrolan ini.. "
            "Bukan berarti obrolan ini melanggar hukum...!",
        )


@user_admin
@typing_action
def set_rules(update, context):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    # use python's maxsplit to separate cmd and args
    args = raw_text.split(None, 1)
    if len(args) == 2:
        txt = args[1]
        # set correct offset relative to command
        offset = len(txt) - len(raw_text)
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset
        )

        RULES_DATA.find_one_and_update(
            {'_id': chat_id},
            {"$set": {'rules': markdown_rules}},
            upsert=True)
        update.effective_message.reply_text(
            "Berhasil menetapkan rules untuk grup ini."
        )


@user_admin
@typing_action
def clear_rules(update, context):
    chat_id = update.effective_chat.id
    RULES_DATA.delete_one({'_id': chat_id})
    update.effective_message.reply_text("Rules berhasil dihapus!")


def chat_rules(chat_id):
    data = RULES_DATA.find_one({'_id': int(chat_id)})  # ensure integer
    if data:
        return data["rules"]
    else:
        return False


def __stats__():
    count = RULES_DATA.count_documents({})
    return " ⇝ {} obrolan memiliki rules yang ditetapkan.".format(count)


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    RULES_DATA.find_one_and_update(
        {'_id': chat_id},
        {"$set": {'rules': rules}},
        upsert=True)


def __migrate__(old_chat_id, new_chat_id):
    rules = RULES_DATA.find_one_and_delete({'_id':old_chat_id})
    if rules:
        RULES_DATA.insert_one(
            {'_id': new_chat_id, 'rules': rules["rules"]})


def __chat_settings__(chat_id, user_id):
    return "Obrolan ini telah menetapkan rulesnya: `{}`".format(
        bool(chat_rules(chat_id))
    )


__help__ = """
Setiap obrolan bekerja dengan rules yang berbeda; modul ini akan membantu memperjelas rules tersebut!

 ⇝ /rules: dapatkan rules untuk obrolan ini.

*Hanya Admin:*
 ⇝ /setrules <sebutkan rules anda>: Menetapkan aturan untuk obrolan.
 ⇝ /clearrules: Menghapus rules yang disimpan untuk obrolan.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler(
    "rules", get_rules, filters=Filters.chat_type.groups, run_async=True
)
SET_RULES_HANDLER = CommandHandler(
    "setrules", set_rules, filters=Filters.chat_type.groups, run_async=True
)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
