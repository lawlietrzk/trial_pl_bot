import os
import logging
import asyncio
import traceback
import html
import json
import tempfile
from pathlib import Path
from datetime import datetime
import phonenumbers
import pandas as pd
import numpy as np

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

# async def register_user_if_not_exists(update: Update, context: CallbackContext, user: User):
#     if not db.check_if_user_exists(user.id):
#         db.add_new_user(
#             user.id,
#             update.message.chat_id,
#             username=user.username,
#             first_name=user.first_name,
#             last_name= user.last_name
#         )
#         db.start_new_dialog(user.id)

#     if db.get_user_attribute(user.id, "current_dialog_id") is None:
#         db.start_new_dialog(user.id)

#     if user.id not in user_semaphores:
#         user_semaphores[user.id] = asyncio.Semaphore(1)

#     if db.get_user_attribute(user.id, "current_model") is None:
#         db.set_user_attribute(user.id, "current_model", config.models["available_text_models"][0])

#     # back compatibility for n_used_tokens field
#     n_used_tokens = db.get_user_attribute(user.id, "n_used_tokens")
#     if isinstance(n_used_tokens, int) or isinstance(n_used_tokens, float):  # old format
#         new_n_used_tokens = {
#             "gpt-3.5-turbo": {
#                 "n_input_tokens": 0,
#                 "n_output_tokens": n_used_tokens
#             }
#         }
#         db.set_user_attribute(user.id, "n_used_tokens", new_n_used_tokens)

#     # voice message transcription
#     if db.get_user_attribute(user.id, "n_transcribed_seconds") is None:
#         db.set_user_attribute(user.id, "n_transcribed_seconds", 0.0)



# async def help_handle(update: Update, context: CallbackContext):
#     await register_user_if_not_exists(update, context, update.message.from_user)
#     user_id = update.message.from_user.id
#     db.set_user_attribute(user_id, "last_interaction", datetime.now())
#     await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.HTML)

# async def message_handle(update: Update, context: CallbackContext, message=None, use_new_dialog_timeout=True):
#     _message = message or update.message.text
#     await register_user_if_not_exists(update, context, update.message.from_user)
#     user_id = update.message.from_user.id

#     async def message_handle_fn():
#         is_url = False
#         chat_mode = db.get_user_attribute(user_id, "current_chat_mode")

#         # new dialog timeout
#         if use_new_dialog_timeout:
#             if (datetime.now() - db.get_user_attribute(user_id, "last_interaction")).seconds > config.new_dialog_timeout and len(db.get_dialog_messages(user_id)) > 0:
#                 db.start_new_dialog(user_id)
#                 await update.message.reply_text(f"Starting new dialog due to timeout (<b>{config.chat_modes[chat_mode]['name']}</b> mode) ✅", parse_mode=ParseMode.HTML)
#         db.set_user_attribute(user_id, "last_interaction", datetime.now())

#         #Set chat mode to QA if reddit url is entered
#         if reddit_utils.is_reddit_url(_message):
#             is_url = True
#             db.set_user_attribute(user_id, "current_chat_mode", "QA")
#             chat_mode = db.get_user_attribute(user_id, "current_chat_mode")

#         # in case of CancelledError
#         n_input_tokens, n_output_tokens = 0, 0
#         current_model = db.get_user_attribute(user_id, "current_model")

#         try:
#             # send placeholder message to user
#             placeholder_message = await update.message.reply_text("...")

#             # send typing action
#             await update.message.chat.send_action(action="typing")
#             if _message is None or len(_message) == 0:
#                  await update.message.reply_text("🥲 You sent <b>empty message</b>. Please, try again!", parse_mode=ParseMode.HTML)
#                  return
            
#             dialog_messages = db.get_dialog_messages(user_id, dialog_id=None)
            
#             parse_mode = {
#                 "html": ParseMode.HTML,
#                 "markdown": ParseMode.MARKDOWN
#             }[config.chat_modes[chat_mode]["parse_mode"]]
            
#             redditgpt_instance = langchain_utils.RedditGPT(model=current_model)
            
#             if chat_mode=='QA' and not is_url:
#                 answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed = await redditgpt_instance.send_qa_response(
#                     _message,
#                     dialog_messages=dialog_messages,
#                     user_id = user_id,
#                     chat_mode=chat_mode
#                 )
#                 async def fake_gen():
#                     yield "finished", answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed

#                 gen = fake_gen()
#             else:
#                 gen = redditgpt_instance.send_message(
#                     _message,
#                     dialog_messages=dialog_messages,
#                     user_id=user_id,
#                     chat_mode=chat_mode,
#                     is_url = is_url
#                 )

#             prev_answer = ""
#             async for gen_item in gen:
#                 status, answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed = gen_item
                
#                 answer = answer[:4096]  # telegram message limit

#                 # update only when 100 new symbols are ready
#                 if abs(len(answer) - len(prev_answer)) < 100 and status != "finished":
#                     continue

#                 try:
#                     await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=parse_mode)
#                 except telegram.error.BadRequest as e:
#                     if str(e).startswith("Message is not modified"):
#                         continue
#                     else:
#                         await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)

#                 await asyncio.sleep(0.01)  # wait a bit to avoid flooding

#                 prev_answer = answer

#             # update user data
#             new_dialog_message = {"user": _message, "bot": answer, "date": datetime.now()}
#             db.set_dialog_messages(
#                 user_id,
#                 db.get_dialog_messages(user_id, dialog_id=None) + [new_dialog_message],
#                 dialog_id=None
#             )

#             db.update_n_used_tokens(user_id, current_model, n_input_tokens, n_output_tokens)

#         except asyncio.CancelledError:
#             # note: intermediate token updates only work when enable_message_streaming=True (config.yml)
#             db.update_n_used_tokens(user_id, current_model, n_input_tokens, n_output_tokens)
#             raise

#         except Exception as e:
#             error_text = f"Something went wrong during completion. Reason: {e}"
#             logger.error(error_text)
#             await update.message.reply_text(error_text)
#             return

#         # send message if some messages were removed from the context
#         if n_first_dialog_messages_removed > 0:
#             if n_first_dialog_messages_removed == 1:
#                 text = "✍️ <i>Note:</i> Your current dialog is too long, so your <b>first message</b> was removed from the context.\n Send /new command to start new dialog"
#             else:
#                 text = f"✍️ <i>Note:</i> Your current dialog is too long, so <b>{n_first_dialog_messages_removed} first messages</b> were removed from the context.\n Send /new command to start new dialog"
#             await update.message.reply_text(text, parse_mode=ParseMode.HTML)


#     async with user_semaphores[user_id]:
#         task = asyncio.create_task(message_handle_fn())
#         user_tasks[user_id] = task

#         try:
#             await task
#         except asyncio.CancelledError:
#             await update.message.reply_text("✅ Canceled", parse_mode=ParseMode.HTML)
#         else:
#             pass
#         finally:
#             if user_id in user_tasks:
#                 del user_tasks[user_id]


# async def new_dialog_handle(update: Update, context: CallbackContext):
#     await register_user_if_not_exists(update, context, update.message.from_user)

#     user_id = update.message.from_user.id
#     db.set_user_attribute(user_id, "last_interaction", datetime.now())

#     db.start_new_dialog(user_id)
#     await update.message.reply_text("Starting new dialog ✅")

#     chat_mode = db.get_user_attribute(user_id, "current_chat_mode")
#     await update.message.reply_text(f"{config.chat_modes[chat_mode]['welcome_message']}", parse_mode=ParseMode.HTML)

# def get_chat_mode_menu(page_index: int):
#     n_chat_modes_per_page = config.n_chat_modes_per_page
#     text = f"Select <b>chat mode</b> ({len(config.chat_modes)} modes available):"

#     # buttons
#     chat_mode_keys = list(config.chat_modes.keys())
#     page_chat_mode_keys = chat_mode_keys[page_index * n_chat_modes_per_page:(page_index + 1) * n_chat_modes_per_page]

#     keyboard = []
#     for chat_mode_key in page_chat_mode_keys:
#         name = config.chat_modes[chat_mode_key]["name"]
#         keyboard.append([InlineKeyboardButton(name, callback_data=f"set_chat_mode|{chat_mode_key}")])

#     reply_markup = InlineKeyboardMarkup(keyboard)

#     return text, reply_markup

# async def show_chat_modes_handle(update: Update, context: CallbackContext):
#     await register_user_if_not_exists(update, context, update.message.from_user)

#     user_id = update.message.from_user.id
#     db.set_user_attribute(user_id, "last_interaction", datetime.now())

#     text, reply_markup = get_chat_mode_menu(0)
#     await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# async def show_chat_modes_callback_handle(update: Update, context: CallbackContext):
#      await register_user_if_not_exists(update.callback_query, context, update.callback_query.from_user)

#      user_id = update.callback_query.from_user.id
#      db.set_user_attribute(user_id, "last_interaction", datetime.now())

#      query = update.callback_query
#      await query.answer()

#      page_index = int(query.data.split("|")[1])
#      if page_index < 0:
#          return

#      text, reply_markup = get_chat_mode_menu(page_index)
#      try:
#          await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
#      except telegram.error.BadRequest as e:
#          if str(e).startswith("Message is not modified"):
#              pass

# async def set_chat_mode_handle(update: Update, context: CallbackContext):
#     await register_user_if_not_exists(update.callback_query, context, update.callback_query.from_user)
#     user_id = update.callback_query.from_user.id

#     query = update.callback_query
#     await query.answer()

#     chat_mode = query.data.split("|")[1]

#     db.set_user_attribute(user_id, "current_chat_mode", chat_mode)
#     db.start_new_dialog(user_id)

#     await context.bot.send_message(
#         update.callback_query.message.chat.id,
#         f"{config.chat_modes[chat_mode]['welcome_message']}",
#         parse_mode=ParseMode.HTML
#     )

# async def error_handle(update: Update, context: CallbackContext) -> None:
#     logger.error(msg="Exception while handling an update:", exc_info=context.error)

#     try:
#         # collect error message
#         tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
#         tb_string = "".join(tb_list)
#         update_str = update.to_dict() if isinstance(update, Update) else str(update)
#         message = (
#             f"An exception was raised while handling an update\n"
#             f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
#             "</pre>\n\n"
#             f"<pre>{html.escape(tb_string)}</pre>"
#         )

#         # split text into multiple messages due to 4096 character limit
#         for message_chunk in split_text_into_chunks(message, 4096):
#             try:
#                 await context.bot.send_message(update.effective_chat.id, message_chunk, parse_mode=ParseMode.HTML)
#             except telegram.error.BadRequest:
#                 # answer has invalid characters, so we send it without parse_mode
#                 await context.bot.send_message(update.effective_chat.id, message_chunk)
#     except:
#         await context.bot.send_message(update.effective_chat.id, "Some error in error handler")


async def contact_handler(update: Update, context: CallbackContext):
    user_id_from_message = update.message.from_user.id 
    contact = update.message.contact 
    
    if contact and contact.user_id == user_id_from_message:
        contact_number = np.int64(contact.phone_number)

        user_data_path = 'user_data.csv' 
        df = pd.read_csv(user_data_path)

        if contact_number in df['phone_num'].values:
            df.loc[df['phone_num'] == contact_number, 'logged_in'] = 1
            df.loc[df['phone_num'] == contact_number, 'user_id'] = user_id_from_message
            df.to_csv(user_data_path, index=False) 

            await update.message.reply_text(f"You are logged in!")

            import glob

            directory_path = ""
            file = glob.glob(f"*_pl.csv")[0]
            df = pd.read_csv(file)

            data = float(df.loc[df['user_id'] == user_id_from_message, 'pl'])
            # print(int(data))
            await update.message.reply_text(f"Your Profit/Loss for the week of xx is : {data}")
        else:
            await update.message.reply_text(f"You do not have an account with MT4")
    else:
        await update.message.reply_text("Please share your own contact using the 'Contact' feature.", parse_mode=ParseMode.HTML)


async def start_handle(update: Update, context: CallbackContext):
    await update.message.reply_text(INTRO_TEXT, parse_mode=ParseMode.HTML)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/start", "Login to account")
    ])

# def send_weekly_data(context):
#     import glob

#     directory_path = ""
#     file = glob.glob(f"{directory_path}/*pl.csv")[0]
#     df = pd.read_csv(file)

#     user_id = context.job.context.get('user_id')
#     data = df[df['user_id'] == user_id].iloc[0]['pl'] 

#     bot = context.job.context
    

#     message = f"Weekly data for {datetime.now().strftime('%Y-%m-%d')}: {data}"
    
#     # Send the message containing the weekly data
#     bot.send_message(chat_id=CHAT_ID, text=message)

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
    # job_queue = application.job_queue

    # job_queue.run_weekly(send_weekly_data, datetime.strptime('09:00:00', '%H:%M:%S'), 0, context=updater.bot)
    # job_queue.run_repeating(send_weekly_data, interval=3,)

    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(CommandHandler("start", start_handle, filters=user_filter))

    application.run_polling()


if __name__ == "__main__":
    run_bot()