# import telegram
from telegram import Bot
import config
import asyncio
import glob
import pandas as pd

bot = Bot(token=token)

async def send_weekly_data():
    directory_path = ""
    user_data_df = pd.read_csv(f"{directory_path}/user_data.csv")
    pnl_data_df = pd.read_csv(glob.glob(f"{directory_path}/*pl.csv")[0])

    user_id_df = user_data_df[user_data_df['user_id'].notnull()]
    login_users_with_telegram_logins = list(zip(user_id_df['login_id'], user_id_df['user_id']))

    for login, user_id in login_users_with_telegram_logins:
        pnl_data = pnl_data_df[pnl_data_df['login'] == login].iloc[0]['pl'] 
        date_extracted = pnl_data_df[pnl_data_df['login'] == login].iloc[0]['pl']
        await bot.sendMessage(chat_id=chat_id, text=msg)

    message = f"Weekly data for {datetime.now().strftime('%Y-%m-%d')}: {data}"
    update.message.reply_text(message, chat_id=user_id,parse_mode=ParseMode.HTML)
    # Send the message containing the weekly data
    # bot.send_message(chat_id=CHAT_ID, text=message)


# bot_token = config.telegram_token
# bot = Bot(token=bot_token)

user_id = 5287614815
# message = "Hello bitch"

async def send(msg, chat_id, token):
    
    await bot.sendMessage(chat_id=chat_id, text=msg)
    print('Message Sent!')

# bot.send_message(chat_id=user_id, text=message)

if __name__ == "__main__":
    asyncio.run(send_weekly_data())