# Ferbot, this is a bot for management your group
# This source code copy from UserIndoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2021 FS Project <https://github.com/FS-Project/Ferbot.git>
# 
import os
import datetime
from telegram.ext import CommandHandler
from telegram import Update
from ferbot import dispatcher
from ferbot.modules.helper_funcs.filters import CustomFilters
from ferbot.modules.helper_funcs.alternate import typing_action


@typing_action
def logs(update, context):
    user = update.effective_user
    with open("Ferbot-log.txt", "rb") as f:
        context.bot.send_document(
            document=f,
            filename=f.name,
            chat_id=user.id,
            caption="This logs that I saved",
        )
        update.effective_message.reply_text("I am send log to your pm 💌")


LOG_HANDLER = CommandHandler(
    "logs", logs, filters=CustomFilters.dev_filter, run_async=True
)
dispatcher.add_handler(LOG_HANDLER)
