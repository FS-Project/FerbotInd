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

import html

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from ferbot import LOGGER, dispatcher
from ferbot.modules.disable import DisableAbleCommandHandler
from ferbot.modules.helper_funcs.admin_rights import user_can_ban
from ferbot.modules.helper_funcs.alternate import typing_action
from ferbot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
)
from ferbot.modules.helper_funcs.extraction import extract_user_and_text
from ferbot.modules.helper_funcs.string_handling import extract_time
from ferbot.modules.log_channel import loggable


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def ban(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki izin untuk melakukan itu!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Anda tidak mengarahkan ke pengguna!")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Pengguna tidak ditemukan":
            message.reply_text("Saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(
            "Saya tidak akan melakukan itu ke admin, jangan bertingkah sok lucu!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya tidak akan melakukan itu ke diri saya, Apakah anda gangguan jiwa?")
        return ""

    log = (
        "<b>{}:</b>"
        "\n#BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        context.bot.sendMessage(
            chat.id,
            "{} Selamat tinggal, lain kali jangan bertingkah konyol!".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Pesan tidak ditemukan":
            # Do not reply
            message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Huhhh, saya gagal melakukannya kepada pengguna itu.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_ban(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text(
            "Anda tidak punya hak untuk melakukan itu!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Heei, setidak nya sebutkan satu untuk diblokir...")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Pengguna tidak ditemukan":
            message.reply_text("Saya tidak dapat menemukan pengguna itu")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Weew, Anda yakin memblokir seorang admin?...")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya tidak akan memblokir dri saya sendiri, Anda sepertinya tidak waras!")
        return ""

    if not reason:
        message.reply_text(
            "Anda belum menentukan waktu untuk memblokir pengguna ini!"
        )
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = (
        "<b>{}:</b>"
        "\n#TEMP BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)"
        "\n<b>Time:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
            time_val,
        )
    )
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        message.reply_text(
            "Diblokir! Pengguna telah diblokir selama {}.".format(time_val)
        )
        return log

    except BadRequest as excp:
        if excp.message == "Pesan tidak ditemukan":
            # Do not reply
            message.reply_text(
                "Selamat jalan.. temukan saya lagi setelah {}.".format(time_val), quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Gagal! saya gagal memblokir pengguna ini.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def kick(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak untuk menendang pengguna dari sini!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Pengguna tidak ditemukan":
            message.reply_text("Saya gagal menemukan pengguna itu")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Huhhft, Yakin akan menendang admin?")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Huhh, Saya tidak dapat melaukan itu")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        context.bot.sendMessage(
            chat.id,
            "Temukan saya kembali setelah {}.".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        log = (
            "<b>{}:</b>"
            "\n#KICKED"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {} (<code>{}</code>)".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(member.user.id, member.user.first_name),
                member.user.id,
            )
        )
        if reason:
            log += "\n<b>Alasan:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Get Out!.")

    return ""


@bot_admin
@can_restrict
@loggable
@typing_action
def banme(update, context):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Yeahhh.. saya tidak akan melakukan itu ke admin.")
        return

    res = update.effective_chat.kick_member(user_id)
    if res:
        update.effective_message.reply_text("Sip, Anda benar! Ayo lakukan itu karena sangat menyenangkan..")
        log = (
            "<b>{}:</b>"
            "\n#BANME"
            "\n<b>User:</b> {}"
            "\n<b>ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                user_id,
            )
        )
        return log

    else:
        update.effective_message.reply_text("Huh? Saya gagal :/")


@bot_admin
@can_restrict
@typing_action
def kickme(update, context):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "Yeahhh.. tidak dapat melakukan itu ke admin."
        )
        return

    res = update.effective_chat.unban_member(
        user_id
    )  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Yapp, Anda benar KELUAR! Lakukan itu karena sangat menyenangkan.")
    else:
        update.effective_message.reply_text("Huh? Saya gagal :/")


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def unban(update, context):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text(
            "Anda tidak ada izin melakukan itu!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Pengguna tidak ditemukan":
            message.reply_text("Saya tidak dapat menemukan pengguna itu")
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("Bagaimana saya bisa melakukan itu?, jika saya masih ada disini...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Bagaimana saya bisa melakukan itu?, jika dia masih ada disini...?"
        )
        return ""

    chat.unban_member(user_id)
    message.reply_text("Berhasil! Dia dapat datang kesini lagi!")

    log = (
        "<b>{}:</b>"
        "\n#UNBANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    return log


__help__ = """

Banyak pengguna yang sering melanggar aturan, anda dapat melarang mereka gabun g ke grup anda atau anda ingin mengeluarkan mereka dari grup anda secara mudah!

 × /kickme: Saya akan mengeluarkan mereka yang menggunakan perintah ini
 × /banme: Saya akan melarang mereka gabung lagi jika mereka memakai perintah ini
*Hanya Admin:*
 × /ban : Memblokir pengguna dengan cara membalas pesan mereka
 × /tban  (m/j/h): Blokir pengguna dengan cara membalas pesan mereka. m = menit, j = jam, h = hari.
 × /unban : Membuka blokir pengguna dengan cara membalas pesan mereka
 × /kick : Menendanf pengguna dengan cara membalas pesan mereka

Contoh memblokir pengguna dengan waktu:
`/tban @namapengguna 2j`; Ini akan memblokir pengguna selama 2 jam.
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(
    "ban", ban, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
TEMPBAN_HANDLER = CommandHandler(
    ["tban", "tempban"],
    temp_ban,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
KICK_HANDLER = CommandHandler(
    "kick", kick, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNBAN_HANDLER = CommandHandler(
    "unban", unban, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
KICKME_HANDLER = DisableAbleCommandHandler(
    "kickme", kickme, filters=Filters.chat_type.groups, run_async=True
)
BANME_HANDLER = DisableAbleCommandHandler(
    "banme", banme, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
