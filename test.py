import webull 


from utils import load_config 

config = load_config('config.json')
email = config['webull_email']
password = config['webull_password']
trading_code = config['webull_trading_code']
token = config['telegram_token']

wb = webull.webull()


wb.login(email, password)

wb.get_trade_token(trading_code)

print(wb.get_history_orders())