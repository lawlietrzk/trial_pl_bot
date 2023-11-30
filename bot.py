import os
import logging
import asyncio
import traceback
import html
import json
import tempfile
from pathlib import Path
from datetime import datetime
# import phonenumbers
import pandas as pd
import numpy as np
import glob

import telegram
from telegram import (
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Updater,
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram.constants import ParseMode, ChatAction

import config


logger = logging.getLogger(__name__)

SHARE_OWN_CONTACT_TEXT= """
Please share your own contact using the 'Contact' feature.
"""

LOGIN_UNSUCCESSFUL_TEXT= """
You do not have an account with Exness MT4
"""

LOG_IN_SUCCESSFUL_TEXT= """
Log in successful!
"""

POST_LOGIN_TEXT = """
You will receive PnL updates every Tuesday between 9 am to 10 am CST.
"""

INTRO_TEXT = """
Hello! I'm a Trade bot. I provide weekly updates
on your Profit/Loss information from your MT4
account.

To start, login with your contact number by executing
the following steps:

- Select the clip icon
- Select "Contact"
- Type your name
- Select "Share Contact"
"""

async def contact_handler(update: Update, context: CallbackContext):
    user_id_from_message = update.message.from_user.id 
    contact = update.message.contact 
    
    # Check if the phone number belongs to the telegram user
    if contact and contact.user_id == user_id_from_message:
        contact_number = np.int64(contact.phone_number)

        user_data_path = 'user_data.csv' 
        df = pd.read_csv(user_data_path)

        # Check if contact number has an account
        if contact_number in df['phone_num'].values:
            df.loc[df['phone_num'] == contact_number, 'logged_in'] = 1
            df.loc[df['phone_num'] == contact_number, 'user_id'] = str(user_id_from_message)
            df.to_csv(user_data_path, index=False) 

            await update.message.reply_text(LOG_IN_SUCCESSFUL_TEXT, parse_mode=ParseMode.HTML)
            await update.message.reply_text(POST_LOGIN_TEXT, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(LOGIN_UNSUCCESSFUL_TEXT, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(SHARE_OWN_CONTACT_TEXT, parse_mode=ParseMode.HTML)

async def send_messages(context: CallbackContext):
    directory_path = ""
    file = glob.glob(f"*_pl.csv")[0]
    df = pd.read_csv(file)

    user_id_from_message=context._user_id
    print(user_id_from_message)
    print(context._chat_id)

    data = df.loc[df['user_id'] == user_id_from_message, 'pl']

    job = context.job
    await context.bot.send_message(job.data, text=f"Your Profit/Loss for the week of xx is : {data}")
    # await context.bot.send_message(chat_id=context, text=f"Your Profit/Loss for the week of xx is : {data}")

    # await update.message.reply_text(f"Your Profit/Loss for the week of xx is : {data}")

async def start_handle(update: Update, context: CallbackContext):
    await update.message.reply_text(INTRO_TEXT, parse_mode=ParseMode.HTML)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/start", "Login to account")
    ])

def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .post_init(post_init)
        .build()
    )

    user_filter = filters.ALL

    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(CommandHandler("start", start_handle, filters=user_filter))

    application.run_polling()


if __name__ == "__main__":
    run_bot()