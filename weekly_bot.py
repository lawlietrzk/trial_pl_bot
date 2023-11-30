# import telegram
from telegram import Bot
import config
import asyncio
import glob
import pandas as pd

bot = Bot(token=config.telegram_token)

async def send_weekly_data():
    directory_path = ""
    user_data_df = pd.read_csv(f"user_data.csv")
    pnl_data_df = pd.read_csv(glob.glob(f"*pl.csv")[0])

    user_id_df = user_data_df[user_data_df['user_id'].notnull()]
    login_users_with_telegram_logins = list(zip(user_id_df['login'], user_id_df['user_id']))

    for login, user_id in login_users_with_telegram_logins:
        pnl_data = pnl_data_df[pnl_data_df['login'] == login].iloc[0]['pl'] 
        # date_extracted = pnl_data_df[pnl_data_df['login'] == login].iloc[0]['pl']
        await bot.sendMessage(chat_id=user_id, text=str(pnl_data))

if __name__ == "__main__":
    asyncio.run(send_weekly_data())