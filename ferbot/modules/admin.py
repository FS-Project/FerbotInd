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
"""This special for you lazy admeme"""

import html
import os

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from ferbot import dispatcher
from ferbot.modules.connection import connected
from ferbot.modules.disable import DisableAbleCommandHandler
from ferbot.modules.helper_funcs.admin_rights import (
    user_can_changeinfo,
    user_can_pin,
    user_can_promote,
)
from ferbot.modules.helper_funcs.alternate import typing_action
from ferbot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    user_admin,
    ADMIN_CACHE,
)
from ferbot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from ferbot.modules.log_channel import loggable


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def promote(update, context):
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak disini!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ID Pengguna tidak ada!")
        return ""

    user_member = chat.get_member(user_id)
    if (
        user_member.status == "administrator"
        or user_member.status == "creator"
    ):
        message.reply_text("Dia sudah menjadi admin!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Jadikan Saya admin dahulu!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(context.bot.id)

    context.bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
    )

    message.reply_text("Promoted❤️")
    return (
        "<b>{}:</b>"
        "\n#PROMOTED"
        "\n<b>Admin :</b> {}"
        "\n<b>User  :</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name),
        )
    )


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def demote(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak disini!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ID Pengguna tidak ada!")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == "creator":
        message.reply_text("Saya tidak bisa melakukan itu kepada pembuat Grup ini!")
        return ""

    if not user_member.status == "administrator":
        message.reply_text(
            "Dia bukanlah seorang admin!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahhh... Saya tidak akan menurunkan diriku!")
        return ""

    try:
        context.bot.promoteChatMember(
            int(chat.id),
            int(user_id),
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
        )
        message.reply_text("Berhasil dilakukan!")
        return (
            "<b>{}:</b>"
            "\n#DEMOTED"
            "\n<b>Admin :</b> {}"
            "\n<b>User  :</b> {}".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(user_member.user.id, user_member.user.first_name),
            )
        )

    except BadRequest:
        message.reply_text(
            "Gagal! Sepertinya Saya bukan admin disini!"
        )
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def pin(update, context):
    args = context.args
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak untuk menyematkan pesan!")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            context.bot.pinChatMessage(
                chat.id,
                prev_message.message_id,
                disable_notification=is_silent,
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return (
            "<b>{}:</b>"
            "\n#PINNED"
            "\n<b>Admin :</b> {}".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def unpin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak untuk melepas pin pada pesan!")
        return ""

    try:
        context.bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        elif excp.message == "Message to unpin not found":
            message.reply_text(
                "Saya tidak dapat melihat pesan yang disematkan, Mungkin sudah tidak tersemat, atau hal lainya!"
            )
        else:
            raise

    return (
        "<b>{}:</b>"
        "\n#UNPINNED"
        "\n<b>Admin :</b> {}".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@bot_admin
@user_admin
@typing_action
def invite(update, context):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat
    context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
    else:
        if msg.chat.type == "private":
            msg.reply_text("Tidak bisa melakukan itu disini!")
            return ""
        chat = update.effective_chat

    if chat.username:
        msg.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = context.bot.exportChatInviteLink(chat.id)
            msg.reply_text(invitelink)
        else:
            msg.reply_text(
                "Saya tidak memiliki akses ke tautan undangan, coba ubah izin saya!"
            )
    else:
        msg.reply_text(
            "Saya hanya dapat memberi Anda tautan undangan untuk supergrup dan channel saja!"
        )


@typing_action
def adminlist(update, context):
    administrators = update.effective_chat.get_administrators()
    text = "Admin di <b>{}</b>:".format(
        update.effective_chat.title
    )
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "creator":
            text += "\n 🦁 Pembuat:"
            text += "\n • {} \n\n 🦊 Admin:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "administrator":
            text += "\n • {}".format(name)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@bot_admin
@can_promote
@user_admin
@typing_action
def set_title(update, context):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except Exception:
        return

    if not user_id:
        message.reply_text("ID Pengguna tidak ada.")
        return

    if user_member.status == "creator":
        message.reply_text(
            "Dialah yang membuat grup ini, bagaimana saya bisa mengatur title untuknya?"
        )
        return

    if not user_member.status == "administrator":
        message.reply_text(
            "Gagal! Dia bukan admin, jadikan admin untuk memberikan title!"
        )
        return

    if user_id == context.bot.id:
        message.reply_text(
            "Gagal! Saya tidak dapat menetapkan title saya sendiri! Hanya orang yang menjadikan saya admin untuk melakukan itu."
        )
        return

    if not title:
        message.reply_text("Membuat title kosong tidak akan menghasilkan apa-apa!")
        return

    if len(title) > 16:
        message.reply_text(
            "Panjang title lebih dari 16 karakter.\nKurangi menjadi 16 karakter."
        )

    try:
        context.bot.set_chat_administrator_custom_title(
            chat.id, user_id, title
        )
        message.reply_text(
            "Berhasil menetapkan title untuk <b>{}</b> ke <code>{}</code>!".format(
                user_member.user.first_name or user_id, title[:16]
            ),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest:
        message.reply_text(
            "Saya tidak dapat membuat title untuk Dia, karena bukan saya yang menjadikan dia admin!"
        )


@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak untuk mengubah info grup!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Anda hanya dapat mengatur beberapa foto sebagai profil grup!")
            return
        dlmsg = msg.reply_text("Tunggu sebentar...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Berhasil mengganti foto profil grup!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Balas beberapa foto atau file untuk menjadikan nya profil grup!")


@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak untuk menghapus foto profil grup!")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Foto profil grup berhasil dihapus!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak untuk mengubah info grup!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Masukkan beberapa teks untuk membuat nama grup Anda!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Berhasil membuat <b>{title}</b> sebagai nama grup baru!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda tidak memiliki hak untuk mengubah info grup!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Anda perlu membalas beberapa stiker untuk menyetel stiker grup!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(
                f"Berhasil memasang stiker grup baru di {chat.title}!"
            )
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Maaf, karena pembatasan telegram, grup harus memiliki minimal 100 anggota sebelum mereka dapat memiliki stiker grup!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text(
            "Anda perlu membalas beberapa stiker untuk membuat stiker grup!"
        )


@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda tidak memiliki hak untuk mengubah info grup!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Berikan beberapa teks untuk membuat deskripsi grup!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "Deskripsi grup tidak boleh lebih dari 255 karakter!"
            )
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(
            f"Deskripsi grup berhasil diperbarui ke {chat.title}!"
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


@user_admin
@typing_action
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Cache admin disegarkan!")


def __chat_settings__(chat_id, user_id):
    return "Kamu adalah *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )


__help__ = """
Semua hal tentang grup seperti daftar admin, menyematkan atau menggeluarkan anggota dapat dilakukan dengan mudah menggunakan bot.

 × /adminlist : Untuk melihat daftar admin di grup.

*Perintah Admin :*
 × /pin : Untuk menyematkan pesan
         - tambahkan `loud` untuk menyematkan pesan secara diam-diam.
         - tambahkan `notify` atau `violent` untuk memberi pemberitahuan kepada pengguna.
 × /unpin : Untuk melepas pesan yang disematkan saat ini.
 × /invitelink : Untuk mendapatkan link grup.
 × /promote : Untuk menjadikan pengguna sebagai admin.
 × /demote : Untuk menurunkan pengguna sebagai anggota.
 × /settitle : Untuk menetapkan title untuk admin.
 × /setgpic : Untuk mengatur foto profil grup.
 × /delgpic : Untuk menghapus foto profil grup.
 × /setgtitle <teks> : Untuk membuat nama grup baru.
 × /setsticker : Untuk membuat stiker grup.
 × /setdescription : <teks> Untuk membuat deskripsi grup.

*Catatan* : 
- Untuk membuat stiker grup, grup harus memiliki minimal 100 anggota.

Contoh :
- Untuk menjadikan seseorang menjadi admin :
  `/promote @username` : ini akan menjadikan pengguna menjadi admin.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler(
    "pin", pin, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNPIN_HANDLER = CommandHandler(
    "unpin", unpin, filters=Filters.chat_type.groups, run_async=True
)
INVITE_HANDLER = CommandHandler("invitelink", invite, run_async=True)
CHAT_PIC_HANDLER = CommandHandler(
    "setgpic", setchatpic, filters=Filters.chat_type.groups, run_async=True
)
DEL_CHAT_PIC_HANDLER = CommandHandler(
    "delgpic", rmchatpic, filters=Filters.chat_type.groups, run_async=True
)
SETCHAT_TITLE_HANDLER = CommandHandler(
    "setgtitle", setchat_title, filters=Filters.chat_type.groups, run_async=True
)
SETSTICKET_HANDLER = CommandHandler(
    "setsticker", set_sticker, filters=Filters.chat_type.groups, run_async=True
)
SETDESC_HANDLER = CommandHandler(
    "setdescription", set_desc, filters=Filters.chat_type.groups, run_async=True
)

PROMOTE_HANDLER = CommandHandler(
    "promote", promote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
DEMOTE_HANDLER = CommandHandler(
    "demote", demote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)

SET_TITLE_HANDLER = DisableAbleCommandHandler(
    "settitle", set_title, pass_args=True, run_async=True
)
ADMINLIST_HANDLER = DisableAbleCommandHandler(
    "adminlist", adminlist, filters=Filters.chat_type.groups, run_async=True
)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, run_async=True
)


dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)
