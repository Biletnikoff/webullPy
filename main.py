import asyncio
import os
import json
import logging

from telegram import  Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import webull
from utils import refresh_and_save_tokens, message_handler, cancel_all_orders, load_config, login, set_bot_commands, button_handler, send_menu, split_otoco_order

async def main() -> None:
    """Run the bot."""
    # Load configuration
    config = load_config('config.json')
    email = config['webull_email']
    password = config['webull_password']
    trading_code = config['webull_trading_code']
    token = config['telegram_token']

    wb = webull.webull()


    wb.login(email, password)

    wb.get_trade_token(trading_code)

    # print(wb.get_history_orders())

    print('patch not exist')
    # updater = Updater(token)
    # dispatcher = updater.dispatcher
    # dispatcher.add_handler(CommandHandler("menu", send_menu))
    # dispatcher.add_handler(CallbackQueryHandler(button_handler))
    # updater.start_polling()
    # updater.idle()


    try:
        updater = Updater(token)
        def cancel_all_orders_wrapper(update: Update, context: CallbackContext) -> None:
            cancel_all_orders(update, context, wb=wb, trading_code=trading_code)
        def button_handler_wrapper(update: Update, context: CallbackContext) -> None:
            button_handler(update, context, wb=wb , trading_code=trading_code)
        # def split_orders_wrapper(update: Update, context: CallbackContext) -> None:
        #     split_otoco_order(update, context, wb=wb, trading_code=trading_code)
        dispatcher = updater.dispatcher
        dispatcher.user_data['wb'] = wb
        dispatcher.add_handler(CommandHandler("menu", send_menu))
        dispatcher.add_handler(CommandHandler("login", login ))
        dispatcher.add_handler(CommandHandler("cancel_all_orders", cancel_all_orders_wrapper))
        # dispatcher.add_handler(CommandHandler("split orders", split_orders_wrapper))
        dispatcher.add_handler(CallbackQueryHandler(button_handler_wrapper))
        print('bot starting')
        updater.start_polling()
        updater.idle()
    except:
        print('start unsuccessful')
asyncio.run(main())