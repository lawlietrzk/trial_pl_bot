import os
import logging
import html
from pathlib import Path
import pandas as pd

import telegram
from telegram import (
    Update,
    BotCommand
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

import config
import custom_texts

def send_login_id_message(login_ids):
    """
    Gets all login_ids for one phone number and sends message.
    """
    return "You have successfully logged into the following account(s): " +", ".join(login_ids)


async def contact_handler(update: Update, context: CallbackContext):
    user_id_from_message = int(update.message.from_user.id)
    contact = update.message.contact 
    
    # Check if the phone number belongs to the telegram user
    if contact and contact.user_id == user_id_from_message:
        contact_number = str(contact.phone_number).strip('+')

        contact_data_path = 'contact_data.csv' 
        df = pd.read_csv(contact_data_path, dtype={'login': str,
                                                    'contact_number' : str,
                                                    'telegram_user_id': str})

        # Check if contact number has an account
        if contact_number in df['contact_number'].values:
            df.loc[df['contact_number'] == contact_number, 'telegram_user_id'] = str(user_id_from_message)
            login_ids = df.loc[df['contact_number'] == contact_number, 'login'].tolist()

            # Store Telegram user_id for the corresponding contact number
            df.to_csv(contact_data_path, index=False) 

            # Send Log in successful messages
            await update.message.reply_text(custom_texts.LOGIN_SUCCESSFUL_TEXT, parse_mode=ParseMode.HTML)
            await update.message.reply_text(send_login_id_message(login_ids), parse_mode=ParseMode.HTML)
            await update.message.reply_text(custom_texts.POST_LOGIN_TEXT, parse_mode=ParseMode.HTML)
        else:
            # If contact number of the texter doesn't exist in contact_data.csv
            await update.message.reply_text(custom_texts.LOGIN_UNSUCCESSFUL_TEXT, parse_mode=ParseMode.HTML)
    else:
        # If contact has shared someone else's contact number
        await update.message.reply_text(custom_texts.SHARE_OWN_CONTACT_TEXT, parse_mode=ParseMode.HTML)


async def start_handle(update: Update, context: CallbackContext):
    """
    Response to "/start" command or 
    when the user interacts with the chatbot for the first time
    """
    await update.message.reply_text(custom_texts.INTRO_TEXT, parse_mode=ParseMode.HTML)

async def post_init(application: Application):
    """
    Creates command menu
    """
    await application.bot.set_my_commands([
        BotCommand("/start", custom_texts.START_HINT)
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

    # Catches all texts of the type CONTACT
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Catches all "/start" command
    application.add_handler(CommandHandler("start", start_handle, filters=user_filter))

    application.run_polling()


if __name__ == "__main__":
    run_bot()