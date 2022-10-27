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

from telegram import Message
from telegram.ext import MessageFilter

from ferbot import SUPPORT_USERS, SUDO_USERS, DEV_USERS


class CustomFilters(object):
    class _Supporters(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user
                and message.from_user.id in SUPPORT_USERS
                or message.from_user
                and message.from_user.id in SUDO_USERS
                or message.from_user
                and message.from_user.id in DEV_USERS
            )

    support_filter = _Supporters()

    class _Sudoers(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user
                and message.from_user.id in SUDO_USERS
                or message.from_user
                and message.from_user.id in DEV_USERS
            )

    sudo_filter = _Sudoers()

    class _Devs(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user and message.from_user.id in DEV_USERS
            )

    dev_filter = _Devs()

    class _MimeType(MessageFilter):
        def __init__(self, mimetype):
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message: Message):
            return bool(
                message.document
                and message.document.mime_type == self.mime_type
            )

    mime_type = _MimeType

    class _HasText(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.text
                or message.sticker
                or message.photo
                or message.document
                or message.video
            )

    has_text = _HasText()
