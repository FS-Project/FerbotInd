# Ferbot, this is a bot for management your group
# This source code copy from UserIndoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2022 FS Project <https://github.com/FS-Project/FerbotInd.git>
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

import html
from typing import Optional

from telegram import Chat, ChatPermissions, Message, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import mention_html

from ferbot import dispatcher
from ferbot.modules.connection import connected
from ferbot.modules.helper_funcs.alternate import send_message, typing_action
from ferbot.modules.helper_funcs.chat_status import is_user_admin, user_admin
from ferbot.modules.helper_funcs.string_handling import extract_time
from ferbot.modules.log_channel import loggable
from ferbot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3

@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = "{} Telah dikeluarkan!".format(
                mention_html(user.id, user.first_name),
            )
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "{} Telah dikeluarkan!".format(
                mention_html(user.id, user.first_name),
            )
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "{} Telah dibisukan!".format(
                mention_html(user.id, user.first_name),
            )
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "Telah diban selama {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Telah dibisukan selama {}".format(getvalue)
            tag = "TMUTE"
        send_message(
            update.effective_message,
            "{} Telah melakukan spam!".format(execstrings),
        )

        return (
            "<b>{} : </b>"
            "\n#{}"
            "\n<b>User : </b>{}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            )
        )

    except BadRequest:
        msg.reply_text(
            "Saya tidak memiliki izin disini, silahkan berikan izin! "
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{} : </b>"
            "\n#INFO"
            "\nTidak memiliki izin untuk melakukan pembisuan anggota!".format(
                chat.title
            )
        )

@user_admin
@loggable
@typing_action
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini hanya dapat dilakukan di grup!",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat_id, 0)
            if conn:
                text = (
                    "Antiflood telah dinonaktifkan di {}.".format(chat_name)
                )
            else:
                text = ("Antiflood telah dinonaktifkan.")
            send_message(message, text, parse_mode="markdown")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "Antiflood telah dinonaktifkan di {}.".format(chat_name)
                    )
                else:
                    text = message.reply_text("Antiflood telah dinonaktifkan.")
                return (
                    "<b>{} :</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin :</b> {}"
                    "\nAntiflood telah dinonaktifkan.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                    )
                )

            elif amount < 3:
                send_message(
                    update.effective_message,
                    "Jika ingin menggunakan Antiflood masukan angka harus lebih dari 3, Jika ingin dinonaktifkan masukan angka 0!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = (
                        "Anti-flood berhasil diatur menjadi {} di grup: {}".format(
                            amount, chat_name
                        )
                    )
                else:
                    text = (
                        "Anti-flood diatur menjadi {}!".format(
                            amount
                        )
                    )
                send_message(
                    update.effective_message, text, parse_mode="markdown"
                )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin :</b> {}"
                    "\nAntiflood diatur menjadi <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        amount,
                    )
                )

        else:
            message.reply_text(
                "Gagal! harap gunakan angka, 'off' atau 'no'"
            )
    else:
        message.reply_text(
            (
                "Gunakan `/setflood <angka>` untuk menggunakan anti-flood.\nAtau gunakan `/setflood off` untuk menonaktifkan antiflood!."
            ),
            parse_mode="markdown",
        )
    return ""


@typing_action
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini hanya dapat dilakukan di grup!",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = (
                "Tidak ada pembatasan di grup {}!".format(chat_name)
            )
        else:
            text = ("Tidak ada pembatasan di sini")
    else:
        if conn:
            text = (
                "Saya diatur membatasi {} pesan beruntun di {}.".format(
                    limit, chat_name
                )
            )
        else:
            text = (
            "Saya diatur membatasi pesan sebanyak {} disini.".format(
                    limit
                )
            )
    send_message(msg, text, parse_mode="markdown")


@user_admin
@loggable
@typing_action
def set_flood_mode(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini hanya dapat dilakukan di grup!",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = ("Anda harus menentukan waktu untuk mengatur antiflood ke tban!\nContoh, `/setfloodmode tban 30m`.\n"
                "Contoh waktu :\n5m = 5 Menit,\n3h = 3 Jam,\n6d = 6 Hari,\n5w = 5 Minggu."
                )
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tban dengan waktu {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = ("Anda harus menentukan waktu untuk mengatur antiflood ke tban!\nContoh, `/setfloodmode tmute 30m`.\n"
                "Contoh waktu :\n5m = 5 Menit,\n3h = 3 Jam,\n6d = 6 Hari,\n5w = 5 Minggu."
                )
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tmute dengan waktu {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "Gunakan ban/kick/mute/tban/tmute saja!",
            )
            return
        if conn:
            send_message(
                msg,
                "Hukuman bagi yang melakukan spam diatur ke {} digrup {}.".format(
                    settypeflood, chat_name
                ),
            )
        else:
            send_message(
                msg,
                "Hukuman bagi yang melakukan spam diatur ke {}".format(
                    settypeflood
                ),
            )
        return (
            "<b>{} :</b>\n"
            "<b>Admin :</b> {}\n"
            "Telah mengatur antiflood. Anggota akan di {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban for {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute for {}".format(getvalue)
        if conn:
            msg.reply_text(
                "Hukuman bagi yang melakukan spam diatur ke {} digrup {}.".format(
                    settypeflood, chat_name
                )
            )
        else:
            msg.reply_text(
                "Hukuman bagi yang melakukan spam diatur ke {}".format(
                    settypeflood
                )
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Tidak mengatur antiflood!"
    else:
        return "Antiflood diatur ke `{}`.".format(limit)


__help__ = """
Antiflood berfungsi untuk membatasi anggota grup yang melakukan pesan beruntun atau spam di grup.

Jika anggota telah melebihi batas yang diatur, anggota akan diberi hukuman sesuai yang diatur oleh admin grup.

 × /flood: Untuk melihat berapa batas pesan yang telah diatur.

*Perintah Admin*:

 × /setflood <angka/'no'/'off'> : Untuk aktifkan / nonaktifkan pembatasan pesan.
 × /setfloodmode <ban/kick/mute/tban/tmute> <waktu> : Untuk mengatur hukuman dan waktunya.

 Catatan :
 - Waktu harus diisi ketika Anda mengatur hukuman ke tban / tmute!

Contoh waktu :
 5m = 5 Menit
 6h = 6 Jam
 3d = 3 Hari
 1w = 1 Minggu

Contoh :
 - Mengatur hukuman ke bisukan selama 1 hari :
   - `/setfloodmode tmute 1d`
 """

__mod_name__ = "Antiflood"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.chat_type.groups,
    check_flood,
    run_async=True,
)
SET_FLOOD_HANDLER = CommandHandler(
    "setflood", set_flood, pass_args=True, run_async=True
)  # , filters=Filters.chat_type.groups)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, pass_args=True, run_async=True
)  # , filters=Filters.chat_type.groups)
# , filters=Filters.chat_type.groups)
FLOOD_HANDLER = CommandHandler("flood", flood, run_async=True)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
