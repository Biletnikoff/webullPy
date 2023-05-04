import os
import json
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
import webull

def load_config(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)

def cancel_all_orders(wb, account_id, update: Update, context: CallbackContext) -> None:
    orders = wb.get_option_orders(account_id, 'working')

    for order in orders:
        wb.cancel_option_order(account_id, order['orderId'])
        update.message.reply_text(f"Cancelled order {order['orderId']}")

def login(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Please send me the MFA code you received:")
    context.user_data['state'] = 'awaiting_mfa_code'


def refresh_and_save_tokens(wb, token_file):
    refreshed_tokens = wb.refresh_login()
    with open(token_file, 'w') as f:
        json.dump({'refreshToken': refreshed_tokens['refreshToken'], 'accessToken': refreshed_tokens['accessToken']}, f)
    

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
