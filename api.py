import requests



def cancel_option_orders(wb, order_id):
    # preint wb objects keys
    # print(wb.__dict__)
    return f'{wb._urls.base_trade_url}/v2/option/cancelOrder/{order_id}'

def replace_option_orders(self, wb, account_id):
    return f'{wb._urls.base_trade_url}/v2/option/replaceOrder/{account_id}'

def cancel_option_order( wb, account_id, order_id):
    '''
    Historical orders, can be cancelled or filled
    status = Cancelled / Filled / Working / Partially Filled / Pending / Failed / All
    '''
    data = {
        'orderId': order_id,

    }
    headers = wb.build_req_headers(include_trade_token=True, include_time=True)
    response = requests.post(cancel_option_orders(wb, order_id), json=data, headers=headers, timeout=wb.timeout)
    print(response.__dict__)
    # if response.status_code != 200:
        # raise Exception('replace_option_order failed', response.status_code, response.reason)
    return response.json()