import os
import json
import logging
from venv import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
import webull
from api import cancel_option_order

def load_config(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)


def get_order_prep(wb:webull,trading_code, status='All'):
    wb.get_trade_token(trading_code)
    orders = wb.get_history_orders(status)
    return orders

def send_cancel_order_message(update: Update, context: CallbackContext, wb: webull, trading_code, ticker) -> None:
    orders = get_order_prep(wb,trading_code, 'Working')
    for order in orders:
        if order['comboId'] and order['ticker'] == ticker and order['comboType'] == 'MASTER':
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='cancel_order'),
                    InlineKeyboardButton("No", callback_data='cancel_order_no'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                f"Are you sure you want to cancel order {order['orderId']}?",
                reply_markup=reply_markup
            )
            return
    update.message.reply_text(
        f"Unable to find order for {ticker}"
    )

def select_ticker_to_cancel_prompt(update: Update, context: CallbackContext, wb: webull, trading_code) -> None:
    orders = get_order_prep(wb,trading_code, 'Working')
    keyboard = []
    for order in orders:
        if order['comboId'] and order['comboType'] == 'MASTER':
            keyboard.append([InlineKeyboardButton(order['ticker'], callback_data=f'cancel_order_{order["ticker"]}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"Select a ticker to cancel",
        reply_markup=reply_markup
    )


#TODO: refactor two functions below to be more DRY-friendly 
def cancel_orders_by_ticker(update: Update, context: CallbackContext, wb: webull, trading_code, ticker) -> None:
    orders = get_order_prep(wb,trading_code, 'Working')
    for order in orders:
        if order['comboId'] and order['ticker'] == ticker and order['comboType'] == 'MASTER':
            canceled_order = wb.cancel_order_otoco(order['orderId'])
            # Check if the order was successfully canceled greater than 0
            if canceled_order.get('success', False) and canceled_order['success'] > 0:
                edit_message(update, context, text=f"Cancelled order {order['orderId']}")
            else:
                edit_message(update, context, text=f"Unable to Cancelled order {order['orderId']}")

def cancel_all_orders( update: Update, context: CallbackContext, wb: webull ,trading_code) -> None:
    orders = group_by_combo_id(get_order_prep(wb,trading_code, 'All'))
    for order in orders:
        #check if order is an OTOCO order   
        if order['comboId']:
            master = order['suborders'][0]['orders'][0]
            stop = order['suborders'][1]['orders'][0]
            profit = order['suborders'][2]['orders'][0]

            order_id1 = master['orderId']
            order_id2 = stop['orderId']
            order_id3 = profit['orderId']
            wb.cancel_order(order_id1)
            canceled_order_profit = wb.cancel_order(order_id2)
            canceled_order_stop = wb.cancel_order(order_id3)
            print(canceled_order_profit)
            # Check if the order was successfully canceled greater than 0
            if canceled_order_profit.get('success', False) and canceled_order_profit['success'] > 0:
               edit_message(update, context, text=f"Cancelled order {order['comboId']}")
            else: 
                print(canceled_order_profit)
                edit_message(update, context, text=f"Unable to Cancelled order {order['comboId']}")

def split_option_order(update: Update, context: CallbackContext, wb: webull, trading_code) -> None:
    open_option_orders = group_by_combo_id(get_order_prep(wb,trading_code, 'All'))
    for order in open_option_orders:
        master = order['suborders'][0]['orders'][0]
        stop = order['suborders'][1]['orders'][0]
        profit = order['suborders'][2]['orders'][0]
        #
        print('adsfljsdklj>>')
        # Calculate the new quantity for the new and modified orders
        original_quant = master['totalQuantity']
        
        # string to number
        string_original_quant = int(original_quant)

        # new_quant = string_original_quant // 2
        modified_quant = string_original_quant - 1

        # Get the existing prices
        existing_price = master['lmtPrice']
        existing_stop_loss_price = stop['auxPrice']
        existing_limit_profit_price = profit['lmtPrice']

        stop = order['suborders'][1]['orders'][0]
        profit = order['suborders'][2]['orders'][0]
        canceled_order_profit = wb.cancel_order(profit['orderId'])
        canceled_order_stop = wb.cancel_order(stop['orderId'])
        modified_order_profit = wb.modify_order_option(
                    order=profit,
                    stpPrice=existing_stop_loss_price,
                    lmtPrice=existing_limit_profit_price,
                    enforce='DAY',
                    quant=modified_quant
                )
        modified_order_stop = wb.modify_order_option(
                    order=stop,
                    stpPrice=existing_stop_loss_price,
                    lmtPrice=existing_limit_profit_price,
                    enforce='DAY',
                    quant=modified_quant
        )
        print(modified_order_profit)
        return modified_order_profit

def split_otoco_order(update: Update, context: CallbackContext, wb: webull, trading_code) -> None:
    orders = group_by_combo_id(get_order_prep(wb,trading_code, 'Working'))
    for order in orders:
        # Check if the order is an OTOCO order
        if order['comboId']:
            # Get the order IDs for the original OTOCO order
            master = order['suborders'][0]['orders'][0]
            stop = order['suborders'][1]['orders'][0]
            profit = order['suborders'][2]['orders'][0]

            order_id1 = master['orderId']
            order_id2 = stop['orderId']
            order_id3 = profit['orderId']

            # Calculate the new quantity for the new and modified orders
            original_quant = master['totalQuantity']
            
            # string to number
            string_original_quant = int(original_quant)

            new_quant = string_original_quant // 2
            modified_quant = string_original_quant - new_quant

            # Get the existing prices
            existing_price = master['lmtPrice']
            existing_stop_loss_price = stop['auxPrice']
            existing_limit_profit_price = profit['lmtPrice']

            cancel_all_order

            # Modify the existing OTOCO order with the modified quantity
            if modified_quant > 0:
                modified_order = wb.modify_order_option(
                    order_id1=order_id1,
                    order_id2=order_id2,
                    order_id3=order_id3,
                    stock=master['symbol'],
                    price=existing_price,
                    stpPrice=existing_stop_loss_price,
                    lmtPrice=existing_limit_profit_price,
                    time_in_force='DAY',
                    quant=modified_quant
                )
                print(modified_order)
                print(existing_stop_loss_price, existing_limit_profit_price)
            # Check if the modified order was successful
                if modified_order.get('success', True):
                    # Place the new OTOCO order with the new quantity
                    new_order = wb.place_order_otoco(
                        stock=master['symbol'],
                        price=None,
                        stop_loss_price=existing_stop_loss_price,
                        limit_profit_price=existing_limit_profit_price,
                        time_in_force='DAY',
                        quant=new_quant
                    )
                    print('----------------------------------------------------------------')
                    print(new_order)
                    # Notify the user about the modified and new orders
                    edit_message(update, context, text=f"Modified order {order['comboId']} to {modified_order['comboId']}")
                    edit_message(update, context, text=f"Placed new order {order_id1}")
    
                else:
                   edit_message(update, context, text=f"Failed to modify the existing OTOCO order -  {order_id1} -")
            else:
               edit_message(update, context, text=f"Quantity too small. Failed to modify the existing OTOCO order.{order_id1}")


def login(update: Update, context: CallbackContext) -> None:
    config = load_config('config.json')
    email = config['webull_email']
    password = config['webull_password']
    did = config['webull_did']
    # trading_code = config['webull_trading_code']
    
    context.user_data['email'] = email
    context.user_data['password'] = password
    context.user_data['token_file'] = 'webull_token.json'

    wb = webull.webull()
    wb._did  = did
    # wb._set_did(did)

    login_response = wb.login(email, password)
    print(wb._get_did())
    account_id = wb.get_account_id()
    print(email, password)
    context.user_data['account_id'] = account_id
    context.user_data['wb'] = wb
    query = update.callback_query
    query.edit_message_text("Logged In")
    print(context.user_data, login_response)
    print(wb._access_token)
    context.user_data['access']
    # with open(context.user_data['token_file'], 'w') as f:
    #     tokens = json.load(f)
    #     tokens['refreshToken'] = login_response['refreshToken']
    #     f.seek(0)  # Move the file pointer to the beginning
    #     f.truncate()  # Clear the file content
    #     json.dump(tokens, f)


def refresh_and_save_tokens(wb, token_file):
    refreshed_tokens = wb.refresh_login()
    if 'refreshToken' in refreshed_tokens and 'accessToken' in refreshed_tokens:
        with open(token_file, 'w') as f:
            json.dump({'refreshToken': refreshed_tokens['refreshToken'],
                       'accessToken': refreshed_tokens['accessToken']}, f)
    else:
        print("Error: refreshToken or accessToken not found in the response.")

def handle_mfa_code(wb, email, password, account_id, token_file, mfa_code: str, update: Update, context: CallbackContext) -> None:
    security_question_id = '1001'
    security_question_answer = 'XXXX'

    device_name = 'Desktop'

    login_response = wb.login(email, password, device_name, mfa_code, security_question_id, security_question_answer)

    if 'accessToken' not in login_response:
        update.message.reply_text("Login failed. Check the MFA code you provided.")
        return

    with open(token_file, 'w') as f:
        json.dump({'refreshToken': login_response['refreshToken']}, f)

    update.message.reply_text("Login successful!")

def get_security_question(wb, email):
    return wb.get_security(email)

def message_handler(wb, email, password, token_file, update: Update, context: CallbackContext) -> None:
    if 'state' in context.user_data:
        if context.user_data['state'] == 'awaiting_mfa_code':
            mfa_code = update.message.text
            context.user_data['mfa_code'] = mfa_code

            security_question = get_security_question(wb, email)
            update.message.reply_text(f"Please answer the security question: {security_question[0]['questionName']}")
            context.user_data['state'] = 'awaiting_security_answer'
            context.user_data['security_question_id'] = security_question[0]['questionId']

        elif context.user_data['state'] == 'awaiting_security_answer':
            security_question_answer = update.message.text
            security_question_id = context.user_data['security_question_id']
            mfa_code = context.user_data['mfa_code']

            wb_result = handle_mfa_code(wb, email, password, token_file, mfa_code, security_question_id, security_question_answer)
            if wb_result is not None:
                update.message.reply_text("Login successful!")
            else:
                update.message.reply_text("Login failed. Check the MFA code and security question answer you provided.")
            context.user_data.pop('state')
            context.user_data.pop('security_question_id')
            context.user_data.pop('mfa_code')
            
def set_bot_commands(bot):
    bot_commands = [
        ('login', 'Login to Webull'),
        ('cancel_all_orders', 'Cancel all option orders'),
        ('split_orders', 'Split orders into smaller orders'),
        # Add more commands here, each in the format ('command', 'Description')
    ]

    command = telegram.BotCommand("start","To start a process")
    # commands = [telegram.BotCommand(command=cmd, description=desc) for cmd, desc in bot_commands]
    bot.set_my_commands(command)



def send_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Login", callback_data="login"),
            InlineKeyboardButton("Cancel All Orders", callback_data="cancel_all_orders"),
            InlineKeyboardButton("Split Orders", callback_data="split_orders"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Please choose a command:", reply_markup=reply_markup)


def button_handler(update: Update, context: CallbackContext, wb, trading_code) -> None:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    query.answer()

    command = query.data

    if command == "login":
        login(update, context)
    elif command == "split_orders":
        print('split_orders')
        split_option_order(update, context, wb, trading_code=trading_code)
    elif command == "cancel_all_orders":
        print(context.user_data)
        cancel_all_orders(update, context, wb, trading_code=trading_code)

def edit_message(update, context, text=None, reply_markup=None):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    current_text = update.callback_query.message.text
    current_reply_markup = update.callback_query.message.reply_markup

    # Check if the new text and reply markup are the same as the current text and reply markup
    # if text == current_text and reply_markup == current_reply_markup:
    #     logger.warning("Message is not modified: specified new message content and reply markup "
    #                    "are exactly the same as a current content and reply markup of the message")
    #     return

    context.bot.send_message(chat_id=chat_id, text=text,
                                  reply_markup=reply_markup)
    



def group_by_combo_id(orders):
    combo_map = {}

    for order in orders:
        combo_id = order["comboId"]

        if combo_id in combo_map:
            combo_map[combo_id]["suborders"].append(order)
        else:
            combo_map[combo_id] = {"comboId": combo_id, "suborders": [order]}

    return list(combo_map.values())



