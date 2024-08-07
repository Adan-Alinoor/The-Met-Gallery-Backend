import base64
from datetime import datetime
import os
from flask import Flask, request, jsonify
import requests
from flask_migrate import Migrate
from flask_restful import Resource, Api
from models import db, User, Product, Cart, CartItem, Order, Payment,OrderItem
import logging

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables for M-Pesa
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
SHORTCODE = os.getenv('SHORTCODE')
LIPA_NA_MPESA_ONLINE_PASSKEY = os.getenv('LIPA_NA_MPESA_ONLINE_PASSKEY')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

def get_mpesa_access_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = CONSUMER_KEY
    consumer_secret = CONSUMER_SECRET
    api_key = f"{consumer_key}:{consumer_secret}"
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(api_key.encode()).decode()
    }
    response = requests.get(api_url, headers=headers)
    
    logging.debug(f"Status Code: {response.status_code}")
    logging.debug(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        json_response = response.json()
        return json_response['access_token']
    else:
        raise Exception(f"Error getting access token: {response.text}")

def generate_password(shortcode, passkey):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8'), timestamp

class MpesaPaymentResource(Resource):
    def process_payment(self, payment_data):
        user_id = payment_data.get('user_id')
        order_id = payment_data.get('order_id')
        phone_number = payment_data.get('phone_number')
        amount = payment_data.get('amount')

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        order = Order.query.get(order_id)
        if not order:
            return {'error': 'Order not found'}, 404

        # Create a new Payment record
        payment = Payment(user_id=user.id, order_id=order.id, amount=amount, phone_number=phone_number)
        db.session.add(payment)
        db.session.commit()

        # Call M-Pesa API to initiate payment
        access_token = get_mpesa_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        password, timestamp = generate_password(SHORTCODE, LIPA_NA_MPESA_ONLINE_PASSKEY)
        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://ab30-102-214-74-3.ngrok-free.app/callback",  # Replace with your callback URL
            "AccountReference": f"Order{order.id}",
            "TransactionDesc": "Payment for order"
        }

        try:
            response = requests.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                headers=headers,
                json=payload
            )

            logging.debug(f'M-Pesa API Response: {response.text}')
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling M-Pesa API: {e}')
            return {'error': 'Failed to connect to M-Pesa API'}, 500
        except ValueError:
            logging.error(f'Invalid JSON response: {response.text}')
            return {'error': 'Invalid response from M-Pesa API'}, 500

        if response_data.get('ResponseCode') == '0':
            payment.transaction_id = response_data['CheckoutRequestID']
            payment.status = 'initiated'
            db.session.commit()
            return {'message': 'Payment initiated successfully'}, 201
        else:
            return {'error': 'Failed to initiate payment'}, 400

    def post(self):
        data = request.get_json()
        return self.process_payment(data)

@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    # Log the incoming callback data for debugging
    logging.debug(f'Callback Data: {data}')

    if not data:
        logging.error("No data received in callback")
        return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
    
    # Process the callback data and update payment status
    try:
        stk_callback = data['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']
        result_desc = stk_callback['ResultDesc']
    except KeyError as e:
        logging.error(f'Missing key in callback data: {e}')
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid data format"}), 400

    # Log the extracted callback data
    logging.debug(f'CheckoutRequestID: {checkout_request_id}')
    logging.debug(f'ResultCode: {result_code}')
    logging.debug(f'ResultDesc: {result_desc}')

    # Find the corresponding payment record
    payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()
    if payment:
        logging.debug(f'Payment record found: {payment.id}')
        if result_code == 0:
            payment.status = 'completed'
            payment.result_desc = result_desc
            payment.timestamp = datetime.now()
        else:
            payment.status = 'failed'
            payment.result_desc = result_desc
            payment.timestamp = datetime.now()
        db.session.commit()
        logging.debug(f'Payment status updated to: {payment.status}')
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200
    else:
        logging.error(f'Payment record not found for CheckoutRequestID: {checkout_request_id}')
        return jsonify({"ResultCode": 1, "ResultDesc": "Payment record not found"}), 404



# ... AddToCartResource, RemoveFromCartResource, ViewCartResource, and CheckoutResource classes ...
#handles cart
class AddToCartResource(Resource):
    def post(self):
        data = request.get_json()

        # Find or create user (assuming a user is authenticated and user_id is available)
        user_id = data.get('user_id')  # Adjust this line as per your authentication system
        if not user_id:
            return {'error': 'User ID is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find or create cart for the user
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()

        # Check if product exists
        product = Product.query.get(data['product_id'])
        if not product:
            return {'error': 'Product not found'}, 404

        # Get the quantity to add
        quantity = data.get('quantity', 1)  # Default to 1 if quantity is not provided

        # Check if the product is already in the cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        if cart_item:
            # Update the quantity if the product is already in the cart
            cart_item.quantity += quantity  # Adjust quantity increment as needed
        else:
            # Add new CartItem if the product is not in the cart
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity, # Adjust quantity as needed
                name = product.name,
                description=product.description,
                price=product.price,
                image=product.image
            )
            db.session.add(cart_item)

        db.session.commit()

        return {'message': 'Product added to cart'}, 201


class RemoveFromCartResource(Resource):
    def post(self):
        data = request.get_json()

        # Find or create user (assuming a user is authenticated and user_id is available)
        user_id = data.get('user_id')  # Adjust this line as per your authentication system
        product_id = data.get('product_id')
        if not user_id or not product_id:
            return {'error': 'User ID and Product ID are required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find the user's cart
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            return {'error': 'Cart not found'}, 404

        # Find the CartItem to be removed
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if not cart_item:
            return {'error': 'Product not found in cart'}, 404

        # Decrement the quantity or remove the CartItem
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        db.session.commit()

        return {'message': 'Product removed from cart'}, 200


class ViewCartResource(Resource):
    def get(self, user_id):
        # Find the user's cart
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return {"error": "Cart not found"}, 404

        # Fetch all cart items
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return {"message": "Cart is empty"}, 200

        # Convert cart items to dictionary format
        cart_items_list = [item.to_dict() for item in cart_items]
        return {'items': cart_items_list}, 200
    
    
#handles checkout
class CheckoutResource(Resource):
    def post(self):
        data = request.get_json()

        user_id = data.get('user_id')
        if not user_id:
            return {'error': 'User ID is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart or not cart.items:
            return {'error': 'Cart is empty'}, 400

        order = Order(user_id=user.id)
        db.session.add(order)
        db.session.commit()

        total_amount = 0
        for item in cart.items:
            total_amount += item.price * item.quantity
            order_item = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.price)
            db.session.add(order_item)

        db.session.commit()

        payment_data = {
            'user_id': user.id,
            'order_id': order.id,
            'phone_number': data.get('phone_number'),
            'amount': total_amount
        }

        # Initiate payment through M-Pesa
        mpesa_resource = MpesaPaymentResource()
        payment_response = mpesa_resource.process_payment(payment_data)

        if payment_response[1] != 201:
            return {'error': 'Failed to initiate payment'}, 400

        # Clear the cart
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

        return {
            'message': 'Order created and payment initiated successfully',
            'order_id': order.id,
            'payment_response': payment_response
        }, 201


api.add_resource(MpesaPaymentResource, '/mpesa_payment')
api.add_resource(AddToCartResource, '/add_to_cart')
api.add_resource(RemoveFromCartResource, '/remove_from_cart')
api.add_resource(ViewCartResource, '/view_cart/<int:user_id>')
api.add_resource(CheckoutResource, '/checkout')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5555)
