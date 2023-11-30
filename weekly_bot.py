from telegram import Bot
import config
import asyncio
import glob
import pandas as pd
from datetime import datetime, timedelta

bot = Bot(token=config.telegram_token)

def get_start_date(current_date):
    """
    Get the week start date
    """
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    one_week_ago = date_obj - timedelta(days=7)
    one_week_ago_string = one_week_ago.strftime("%Y-%m-%d")
    return one_week_ago_string

async def send_weekly_data():
    contact_data_df = pd.read_csv(f"contact_data.csv", dtype={'login': str,
                                                              'contact_number' : str,
                                                              'telegram_user_id': str})
    pnl_data_df = pd.read_csv(glob.glob(f"*pl.csv")[0], dtype={'login': str,
                                                              'pnl' : float,
                                                              'date_extracted': str} )

    contact_data_df = contact_data_df[contact_data_df['telegram_user_id'].notnull()]
    current_date = pnl_data_df['date_extracted'][0]
    start_date = get_start_date(current_date)

    # Iterates through all contacts that have interacted with the bot
    for index, row in contact_data_df.iterrows():
        login = row['login']
        user_id = row['telegram_user_id']

        pnl_data = pnl_data_df[pnl_data_df['login'] == login].iloc[0]['pnl'] 
        output_message = f"For account {login}, the PnL from {start_date} to {current_date} is {str(pnl_data)}"

        await bot.sendMessage(chat_id=user_id, text=output_message)

if __name__ == "__main__":
    asyncio.run(send_weekly_data())