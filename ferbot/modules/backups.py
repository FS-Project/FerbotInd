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

import json
import os
import time
from io import BytesIO

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler

# from ferbot.modules.sql import warns_sql as warnssql
from ferbot.modules.no_sql import blacklist_db

# from ferbot.modules.sql import cust_filters_sql as filtersql
# import ferbot.modules.sql.welcome_sql as welcsql
import ferbot.modules.sql.locks_sql as locksql
import ferbot.modules.sql.notes_sql as sql

# from ubotindo.modules.rules import get_rules
from ferbot.modules.rules import chat_rules
from ferbot import DEV_USERS, LOGGER, MESSAGE_DUMP, OWNER_ID, dispatcher
from ferbot.__main__ import DATA_IMPORT
from ferbot.modules.connection import connected
from ferbot.modules.helper_funcs.alternate import typing_action
from ferbot.modules.helper_funcs.chat_status import user_admin
from ferbot.modules.no_sql import disable_db


@user_admin
@typing_action
def import_data(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text(
                "Perintah ini hanya bisa di grup, bukan PM."
            )
            return ""

        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = context.bot.get_file(
                msg.reply_to_message.document.file_id
            )
        except BadRequest:
            msg.reply_text(
                "Ulangi, file ini sepertinya rusak!"
            )
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text(
                "Terdapat lebih dari satu grup di file ini dan id grup tidak sama, bagaimana saya bisa mengimpornya?"
            )
            return

        # Check if backup is this chat
        try:
            if data.get(str(chat.id)) is None:
                if conn:
                    text = "Gagal! File ini berasal dari grup lain, saya tidak bisa melakukan itu ke grup *{}*".format(
                        chat_name
                    )
                else:
                    text = "Gagal! File ini berasal dari grup lain, saya tidak bisa melakukan itu ke grup ini"
                return msg.reply_text(text, parse_mode="markdown")
        except Exception:
            return msg.reply_text("Terdapat masalah saat mengimpor data!")
        # Check if backup is from self
        try:
            if str(context.bot.id) != str(data[str(chat.id)]["bot"]):
                return msg.reply_text(
                    "File dari bot lain tidak disarankan, kemungkinan dapat menyebabkan masalah, dokumen, foto, video, audio, catatan mungkin tidak berfungsi sebagaimana mestinya."
                )
        except Exception:
            pass
        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text(
                "Terjadi kesalahan saat memulihkan data Anda. Prosesnya gagal. Jika Anda mengalami masalah dengan ini, silakan tanya @Fernans1"
            )

            LOGGER.exception(
                "Import for the chat %s with the name %s failed.",
                str(chat.id),
                str(chat.title),
            )
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        if conn:

            text = "Pencadangan berhasil dilakukan di *{}*.".format(chat_name)
        else:
            text = "Pencadangan berhasil dilakukan"
        msg.reply_text(text, parse_mode="markdown")


@user_admin
def export_data(update, context):
    chat_data = context.chat_data
    msg = update.effective_message
    user = update.effective_user
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    current_chat_id = update.effective_chat.id
    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        # chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text(
                "Perintah ini hanya dapat digunakan di grup, bukan PM"
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        # chat_name = update.effective_message.chat.title

    jam = time.time()
    new_jam = jam + 10800
    checkchat = get_chat(chat_id, chat_data)
    if checkchat.get("status"):
        if jam <= int(checkchat.get("value")):
            timeformatt = time.strftime(
                "%J:%M:%D %h/%m/%Y", time.localtime(checkchat.get("value"))
            )
            update.effective_message.reply_text(
                "Anda hanya dapat melakukan itu satu hari sekali!\nAnda dapat melakukan itu setelah `{}`".format(
                    timeformatt
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            if user.id != OWNER_ID or user.id not in DEV_USERS:
                put_chat(chat_id, new_jam, chat_data)
    else:
        if user.id != OWNER_ID or user.id not in DEV_USERS:
            put_chat(chat_id, new_jam, chat_data)

    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    notes = {}
    # button = ""
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    countbtn = 0
    # Notes
    for note in note_list:
        count += 1
        # getnote = sql.get_note(chat_id, note.name)
        namacat += "{}<###splitter###>".format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)
            # keyb = []
            for btn in tombol:
                countbtn += 1
                if btn.same_line:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), True)
                    )
                else:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), False)
                    )
            isicat += (
                "###button###: {}<###button###>{}<###splitter###>".format(
                    note.value, str(buttonlist)
                )
            )
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += "###sticker###:{}<###splitter###>".format(note.file)
        elif note.msgtype == 3:
            isicat += (
                "###file###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                    note.file, note.value
                )
            )
        elif note.msgtype == 4:
            isicat += (
                "###photo###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                    note.file, note.value
                )
            )
        elif note.msgtype == 5:
            isicat += (
                "###audio###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                    note.file, note.value
                )
            )
        elif note.msgtype == 6:
            isicat += (
                "###voice###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                    note.file, note.value
                )
            )
        elif note.msgtype == 7:
            isicat += (
                "###video###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                    note.file, note.value
                )
            )
        elif note.msgtype == 8:
            isicat += "###video_note###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        else:
            isicat += "{}<###splitter###>".format(note.value)
    for x in range(count):
        notes[
            "#{}".format(namacat.split("<###splitter###>")[x])
        ] = "{}".format(isicat.split("<###splitter###>")[x])
    # Rules
    rules = chat_rules(chat_id)
    # Blacklist
    bl = list(blacklist_db.get_chat_blacklist(chat_id))
    # Disabled command
    disabledcmd = list(disable_db.get_all_disabled(chat_id))
    # Filters (TODO)
    """
	all_filters = list(filtersql.get_chat_triggers(chat_id))
	export_filters = {}
	for filters in all_filters:
		filt = filtersql.get_filter(chat_id, filters)
		# print(vars(filt))
		if filt.is_sticker:
			tipefilt = "sticker"
		elif filt.is_document:
			tipefilt = "doc"
		elif filt.is_image:
			tipefilt = "img"
		elif filt.is_audio:
			tipefilt = "audio"
		elif filt.is_voice:
			tipefilt = "voice"
		elif filt.is_video:
			tipefilt = "video"
		elif filt.has_buttons:
			tipefilt = "button"
			buttons = filtersql.get_buttons(chat.id, filt.keyword)
			print(vars(buttons))
		elif filt.has_markdown:
			tipefilt = "text"
		if tipefilt == "button":
			content = "{}#=#{}|btn|{}".format(tipefilt, filt.reply, buttons)
		else:
			content = "{}#=#{}".format(tipefilt, filt.reply)
		print(content)
		export_filters[filters] = content
	print(export_filters)
	"""
    # Welcome (TODO)
    # welc = welcsql.get_welc_pref(chat_id)
    # Locked
    curr_locks = locksql.get_locks(chat_id)
    curr_restr = locksql.get_restr(chat_id)

    if curr_locks:
        locked_lock = {
            "sticker": curr_locks.sticker,
            "audio": curr_locks.audio,
            "voice": curr_locks.voice,
            "document": curr_locks.document,
            "video": curr_locks.video,
            "contact": curr_locks.contact,
            "photo": curr_locks.photo,
            "gif": curr_locks.gif,
            "url": curr_locks.url,
            "bots": curr_locks.bots,
            "forward": curr_locks.forward,
            "game": curr_locks.game,
            "location": curr_locks.location,
            "rtl": curr_locks.rtl,
        }
    else:
        locked_lock = {}

    if curr_restr:
        locked_restr = {
            "messages": curr_restr.messages,
            "media": curr_restr.media,
            "other": curr_restr.other,
            "previews": curr_restr.preview,
            "all": all(
                [
                    curr_restr.messages,
                    curr_restr.media,
                    curr_restr.other,
                    curr_restr.preview,
                ]
            ),
        }
    else:
        locked_restr = {}

    locks = {"locks": locked_lock, "restrict": locked_restr}
    # Warns (TODO)
    # warns = warnssql.get_warns(chat_id)
    # Backing up
    backup[chat_id] = {
        "bot": context.bot.id,
        "hashes": {
            "info": {"rules": rules},
            "extra": notes,
            "blacklist": bl,
            "disabled": disabledcmd,
            "locks": locks,
        },
    }
    baccinfo = json.dumps(backup, indent=4)
    with open("FerbotInd-Bot{}.backup".format(chat_id), "w") as f:
        f.write(str(baccinfo))
    context.bot.sendChatAction(current_chat_id, "upload_document")
    tgl = time.strftime("%J:%M:%D - %h/%m/%Y", time.localtime(time.time()))
    try:
        context.bot.sendMessage(
            MESSAGE_DUMP,
            "*Berhasil mengimpor:*\nGrup: `{}`\nID Grup: `{}`\nDalam: `{}`".format(
                chat.title, chat_id, tgl
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest:
        pass
    context.bot.sendDocument(
        current_chat_id,
        document=open("FerbotInd-Bot{}.backup".format(chat_id), "rb"),
        caption="*Berhasil mencadangkan:*\nGrup: `{}`\nID Grup: `{}`\nDalam: `{}`\n\nCatatan: `FerbotInd-Backup` ini khusus dibuat untuk catatan.".format(
            chat.title, chat_id, tgl
        ),
        timeout=360,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )
    os.remove("FerbotInd-Bot{}.backup".format(chat_id))  # Cleaning file


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    if not value:
        status = False
    else:
        status = True
    chat_data[chat_id] = {"backups": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        value = chat_data[chat_id]["backups"]
        return value
    except KeyError:
        return {"status": False, "value": False}


__mod_name__ = "Backups"

__help__ = """
*Hanya untuk Admin grup:*

 × /import: Balas ke file cadangan untuk diimpor! \
 Perhatikan bahwa file / foto tidak dapat diimpor karena batasan telegram.

 × /export: Membuat file cadangan untuk di impor, yang akan di ekspor adalah: Peraturan, Catatan dll \

"""

IMPORT_HANDLER = CommandHandler("import", import_data, run_async=True)
EXPORT_HANDLER = CommandHandler(
   "export", export_data, pass_chat_data=True, run_async=True
)

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)
