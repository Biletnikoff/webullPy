import webull
from webull import 

def main():
    # Replace these with your Webull email and password
    email = 'your_email@example.com'
    password = 'your_password'

    # Authenticate with Webull
    wb = webull.Webull()
    login_response = wb.login(email, password)

    if 'accessToken' not in login_response:
        print("Login failed. Check your email and password.")
        return

    # Get account ID
    account_id = wb.get_account_id()

    # Get all open option orders
    
    def cancel_open_orders():
        open_orders = wb.get_open_option_orders(account_id)

    # Loop through the orders and cancel each one
        for order in open_orders:
            order_id = order['orderId']
            print(f'Cancelling order: {order_id}')
            cancel_response = wb.cancel_option_order(account_id, order_id)
            if 'success' in cancel_response and cancel_response['success']:
                print(f'Successfully cancelled order: {order_id}')
            else:
                print(f'Failed to cancel order: {order_id}')
            time.sleep(1)  # Add a short delay to avoid overwhelming the API


if __name__ == "__main__":
    main()
