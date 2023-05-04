import asyncio
import os
import json
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import webull
from utils import refresh_and_save_tokens, message_handler, cancel_all_orders, load_config, login

async def main() -> None:
    """Run the bot."""
    # Load configuration
    config = load_config('config.json')
    email = config['webull_email']
    password = config['webull_password']
    token = config['telegram_token']

    wb = webull.webull()

    token_file = 'webull_token.json'

    if not os.path.exists(token_file):
        updater = Updater(token)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("login", login))
        updater.start_polling()
        updater.idle()
    else:
        with open(token_file, 'r') as f:
            tokens = json.load(f)
            wb.refresh_login(tokens['refreshToken'])

        refresh_and_save_tokens(wb, token_file)

        account_id = wb.get_account_id()

        updater = Updater(token)
        dispatcher = updater.dispatcher
        dispatcher.user_data['wb'] = wb
        dispatcher.user_data['account_id'] = account_id

        dispatcher.add_handler(CommandHandler("login", login))
        dispatcher.add_handler(CommandHandler("cancel_all_orders", cancel_all_orders, pass_wb=True,  pass_account_id = True))
        dispatcher.add_handler(MessageHandler(filters.text, message_handler))

        updater.start_polling()
        updater.idle()

asyncio.run(main())