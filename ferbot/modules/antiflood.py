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
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "Banned for {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Sekarang kamu diam selama {}".format(getvalue)
            tag = "TMUTE"
        send_message(
            update.effective_message,
            "Bagus, Saya suka jika anda meramaikan grup ini tapi banjir pesan mu "
            "membuat saya kecewa. {}!".format(execstrings),
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            )
        )

    except BadRequest:
        msg.reply_text(
            "Berikan saya izin agar saya bisa membatasi orang mengirim pesan beruntun di sini! "
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(
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
                "Perintah ini dimaksudkan untuk digunakan dalam grup bukan di PM",
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
                    "Antiflood has been disabled in {}.".format(chat_name)
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
                        "Antiflood has been disabled in {}.".format(chat_name)
                    )
                else:
                    text = message.reply_text("Antiflood telah dinonaktifkan.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
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
                        "Anti-flood berhasil di atur ke {} di grup: {}".format(
                            amount, chat_name
                        )
                    )
                else:
                    text = (
                        "Berhasil memperbarui batas Anti-flood menjadi {}!".format(
                            amount
                        )
                    )
                send_message(
                    update.effective_message, text, parse_mode="markdown"
                )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood to <code>{}</code>.".format(
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
                "Gunakan `/setflood angka` untuk menggunakan anti-flood.\nAtau gunakan `/setflood off` untuk menonaktifkan antiflood!."
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
                "Perintah ini dimaksudkan untuk digunakan dalam grup bukan di PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = (
                "Saya tidak memaksakan pengendalian pesan apa pun di {}!".format(chat_name)
            )
        else:
            text = ("Saya tidak memaksakan pengendalian pesan di sini")
    else:
        if conn:
            text = (
                "Saya saat ini membatasi anggota setelah {} pesan beruntun di {}.".format(
                    limit, chat_name
                )
            )
        else:
            text = (
                "I'm currently restricting members after {} consecutive messages.".format(
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
                "This command is meant to use in group not in PM",
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
                teks = ("It looks like you tried to set time value for antiflood"
                "but you didn't specified time;\nTry, `/setfloodmode tban <timevalue>`.\n"
                "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."
                )
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tban for {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    "It looks like you tried to set time value for antiflood"
                    "but you didn't specified time;\nTry, `/setfloodmode tmute <timevalue>`.\n"
                    "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.",
                )
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tmute for {}".format(args[1])
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
                "Exceeding consecutive flood limit will result in {} in {}!".format(
                    settypeflood, chat_name
                ),
            )
        else:
            send_message(
                msg,
                "Exceeding consecutive flood limit will result in {}!".format(
                    settypeflood
                ),
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Has changed antiflood mode. User will {}.".format(
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
                "Sending more messages than flood limit will result in {} in {}.".format(
                    settypeflood, chat_name
                )
            )
        else:
            msg.reply_text(
                "Sending more message than flood limit will result in {}.".format(
                    settypeflood
                )
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing to flood control."
    else:
        return "Antiflood has been set to`{}`.".format(limit)


__help__ = """
Anda ingin membatasi anggota yang sering mengirim pesan beruntun?.. Tenang semua itu akan saya batasi!

Saya akan membatasi anggota mengirim pesan jika dia telah melebihi batas yang telah ditentukan, jika melebihi anggota akan diberi hukuman yang telah ditentukan

 × /flood: Lihat berapa batas pesan yang telah ditentukan

*Hanya Admin*:

 × /setflood <angka/'no'/'off'>: Aktifkan / nonaktifkan pembatasan pesan.
 × /setfloodmode <ban/kick/mute/tban/tmute> <nilai>: Tentukan apa yang akan terjadi setelah anggota melebihi batas mengirim pesan.

 Note:
 - Nilai harus diisi ketika anda mengatur hukumannya sebagai tban / tmute!

 Nilainya:
 5m = 5 menit
 6h = 6 jam
 3d = 3 hari
 1w = 1 minggu
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
