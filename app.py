
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from models import db, User, Cart, CartItem, Order, Payment, OrderItem, Artwork, ShippingAddress
import bcrypt
import base64
from datetime import datetime
import os
from flask import Flask, request, jsonify
import requests

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import logging
from sqlalchemy.exc import SQLAlchemyError
from auth import user_required, admin_required
from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.ticket import MpesaCallbackResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CALLBACK_SECRET = 'your_secret_key_here'


migrate = Migrate(app, db)
db.init_app(app) 
jwt = JWTManager(app)
api = Api(app)
CORS(app)

class Signup(Resource):
    def post(self):
        args = request.get_json()
        if not all(k in args for k in ('username', 'email', 'password')):
            return {'message': 'Username, email, and password are required'}, 400
        
        role = args.get('role', 'user')  
        hashed_password = bcrypt.hashpw(args['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=args['username'], email=args['email'], password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return {'message': f"{role.capitalize()} created successfully"}, 201
    

class Login(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('email', type=str, required=True, help='Email cannot be blank')
        self.parser.add_argument('password', type=str, required=True, help='Password cannot be blank')

    def post(self):
        args = self.parser.parse_args()
        email = args['email']
        password = args['password']

        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'message': f"{user.role.capitalize()} logged in successfully",
                'access_token': access_token,
                'role': user.role  # Include the user's role in the response
            })
        
        return jsonify({'message': 'Invalid email or password'}), 401


class Logout(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return {'message': f"{user.role.capitalize()} logged out successfully"}, 200

class UserResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at
        })

    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        args = request.get_json()

        if User.query.filter_by(username=args.get('username')).first() and args.get('username') != user.username:
            return {'message': 'Username is already taken'}, 400

        user.username = args.get('username', user.username)
        user.email = args.get('email', user.email)
        if args.get('password'):
            user.password = bcrypt.hashpw(args['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500

        return {'message': 'User updated successfully'}, 200

    @jwt_required()
    def delete(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200

class AdminResource(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        return {'message': 'Admin content accessible'}


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(UserResource, '/user')
api.add_resource(AdminResource, '/admin')





class ArtworkListResource(Resource):
    @user_required
    def get(self):
        try:
            artworks = Artwork.query.all()
            return [artwork.to_dict() for artwork in artworks], 200
        except Exception as e:
            return {"error": str(e)}, 500

    @user_required  # Only authenticated users can post artwork
    def post(self):
        data = request.get_json()
        if not data:
            return {"error": "No input data provided"}, 400
        if not all(k in data for k in ("title", "description", "price", "image")):
            return {"error": "Missing fields in input data"}, 400

        try:
            new_artwork = Artwork(
                title=data['title'],
                description=data['description'],
                price=data['price'],
                image=data['image']
            )
            db.session.add(new_artwork)
            db.session.commit()
            return {"message": "Artwork created", "artwork": new_artwork.to_dict()}, 201
        except Exception as e:
            return {"error": str(e)}, 500

class ArtworkResource(Resource):
    @user_required  
    def get(self, id):
        try:
            artwork = Artwork.query.get_or_404(id)
            return artwork.to_dict(), 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @user_required  
    def put(self, id):
        data = request.get_json()
        if not data:
            return {"error": "No input data provided"}, 400

        try:
            artwork = Artwork.query.get_or_404(id)
            artwork.title = data.get('title', artwork.title)
            artwork.description = data.get('description', artwork.description)
            artwork.price = data.get('price', artwork.price)
            artwork.image = data.get('image', artwork.image)
            db.session.commit()
            return {"message": "Artwork updated", "artwork": artwork.to_dict()}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @user_required  # Allow any authenticated user to delete artwork
    def delete(self, id):
        try:
            artwork = Artwork.query.get_or_404(id)
            db.session.delete(artwork)
            db.session.commit()
            return {"message": "Artwork deleted"}, 200
        except Exception as e:
            return {"error": str(e)}, 500



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

        # Check if artwork exists
        artwork = Artwork.query.get(data['artwork_id'])
        if not artwork:
            return {'error': 'artwork not found'}, 404

        # Get the quantity to add
        quantity = data.get('quantity', 1)  # Default to 1 if quantity is not provided

        # Check if the artwork is already in the cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork.id).first()
        if cart_item:
            # Update the quantity if the artwork is already in the cart
            cart_item.quantity += quantity  # Adjust quantity increment as needed
        else:
            # Add new CartItem if the artwork is not in the cart
            cart_item = CartItem(
                cart_id=cart.id,
                artwork_id=artwork.id,
                quantity=quantity, # Adjust quantity as needed
                title = artwork.title,
                description=artwork.description,
                price=artwork.price,
                image=artwork.image
            )
            db.session.add(cart_item)

        db.session.commit()

        return {'message': 'Artwork added to cart'}, 201


class RemoveFromCartResource(Resource):
    def post(self):
        data = request.get_json()

        # Find or create user (assuming a user is authenticated and user_id is available)
        user_id = data.get('user_id')  # Adjust this line as per your authentication system
        artwork_id = data.get('artwork_id')
        if not user_id or not artwork_id:
            return {'error': 'User ID and artwork ID are required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find the user's cart
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            return {'error': 'Cart not found'}, 404

        # Find the CartItem to be removed
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
        if not cart_item:
            return {'error': 'Artwork not found in cart'}, 404

        # Decrement the quantity or remove the CartItem
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        db.session.commit()

        return {'message': 'Artwork removed from cart'}, 200


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




class Home(Resource):
    def get(self):
        response_dict = {"message": "Welcome to The Met Gallery"}
        return jsonify(response_dict)


# Add the EventsResource class as a resource to the API
api.add_resource(Home, '/')

api.add_resource(EventsResource, '/events', '/events/<int:id>')
api.add_resource(TicketResource, '/tickets')
api.add_resource(MpesaCallbackResource, '/callback')
api.add_resource(BookingResource, '/bookings', '/bookings/<int:id>')
api.add_resource(TicketAdminResource, '/admin/tickets', '/admin/tickets/<int:id>')

api.add_resource(ArtworkListResource, '/artworks')
api.add_resource(ArtworkResource, '/artworks/<int:id>')

# Configure logging
logging.basicConfig(level=logging.DEBUG)


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



def determine_payment_type(payment_data):
    if payment_data.get('order_id'):
        return 'artwork'
    elif payment_data.get('booking_id'):
        return 'event'
    else:
        raise ValueError("Cannot determine payment type from provided data")

def create_payment(payment_data):
    payment_type = determine_payment_type(payment_data)
    
    payment = Payment(
        user_id=payment_data.get('user_id'),
        booking_id=payment_data.get('booking_id'),
        order_id=payment_data.get('order_id') if payment_type == 'artwork' else None,
        amount=payment_data['amount'],
        phone_number=payment_data.get('phone_number'),
        transaction_id=payment_data.get('transaction_id'),
        status=payment_data.get('status'),
        result_desc=payment_data.get('result_desc'),
        payment_type=payment_type
    )
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
        "Amount": payment_data['amount'],
        "PartyA": payment_data['phone_number'],
        "PartyB": SHORTCODE,
        "PhoneNumber": payment_data['phone_number'],
        "CallBackURL": "https://b0ca-102-214-74-3.ngrok-free.app/callback",  # Replace with your callback URL
        "AccountReference": f"Order{payment_data.get('order_id')}",
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



class CheckoutResource(Resource):
    @staticmethod
    def initiate_mpesa_payment(payment_data):
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


        payment = Payment(
            user_id=user.id,
            order_id=order.id,
            amount=amount,

            phone_number=phone_number,
            transaction_id=None,  # Placeholder for the transaction ID
            status='pending',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
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
            "CallBackURL": "https://b0ca-102-214-74-3.ngrok-free.app/callback",  # Replace with your callback URL
            "AccountReference": f"Order{order.id}",
            "TransactionDesc": "Payment for order"
        }

            phone_number=phone_number
        )
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
            "CallBackURL": "  https://ce71-102-214-74-3.ngrok-free.app/callback",  # Replace with your callback URL
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
            response_data = response.json()  # This returns a dict

            if response_data.get('ResponseCode') == '0':
                payment.transaction_id = response_data.get('CheckoutRequestID')
                payment.status = 'initiated'
                payment.transaction_desc = "Payment initiated successfully"
                db.session.commit()
                return {'message': 'Payment initiated successfully', 'transaction_desc': payment.transaction_desc}, 201
            else:
                return {'error': 'Failed to initiate payment'}, 400

        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling M-Pesa API: {e}')
            return {'error': 'Failed to connect to M-Pesa API'}, 500
        except ValueError:
            logging.error(f'Invalid JSON response: {response.text}')
            return {'error': 'Invalid response from M-Pesa API'}, 500

        return create_payment(payment_data)  # Call create_payment function


    def post(self):
        data = request.get_json()

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
            payment.status = 'failed'
            db.session.commit()
            return {'error': 'Failed to initiate payment'}, 400

    @jwt_required()
    def post(self):
        # Extract user ID from JWT
        current_user = get_jwt_identity()
        user_id = current_user.get('id')
        if not user_id:
            return {'error': 'User ID is required'}, 400

        data = request.get_json()
        if not data:
            return {'error': 'No input data provided'}, 400

        phone_number = data.get('phone_number')
        if not phone_number:
            return {'error': 'Phone number is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Check if shipping address exists for the user
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if not shipping_address:
            return {'error': 'Shipping address is required'}, 400

        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart or not cart.items:
            return {'error': 'Cart is empty'}, 400

        selected_items = data.get('items', [])
        if not selected_items:
            return {'error': 'No items selected for checkout'}, 400

        order = Order(user_id=user.id)
        db.session.add(order)

        total_amount = 0
        for selected_item in selected_items:
            artwork_id = selected_item.get('artwork_id')
            quantity = selected_item.get('quantity', 1)

            cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
            if not cart_item or cart_item.quantity < quantity:
                return {'error': f'Invalid quantity for artwork ID {artwork_id}'}, 400

            total_amount += cart_item.price * quantity
            order_item = OrderItem(order_id=order.id, artwork_id=artwork_id, quantity=quantity, price=cart_item.price)
            db.session.add(order_item)

            if cart_item.quantity > quantity:
                cart_item.quantity -= quantity
            else:
                db.session.delete(cart_item)

            db.session.commit()

        payment_data = {
            'user_id': user.id,
            'order_id': order.id,
            'phone_number': phone_number,
            'amount': total_amount
        }


        payment_response = self.initiate_mpesa_payment(payment_data)

        if payment_response[1] != 201:
                db.session.rollback()  # Rollback cart item removal if payment fails
                return {'error': 'Failed to initiate payment'}, 400

        return {
            'message': 'Order created and payment initiated successfully',
            'order_id': order.id,
            'payment_response': payment_response
        }, 201


            # Initiate payment through M-Pesa
            payment_response, status_code = self.initiate_mpesa_payment(payment_data)

            if status_code != 201:
                db.session.rollback()
                return payment_response, 400

            return {
                'message': 'Order placed and payment initiated successfully',
                'order_id': order.id,
                'transaction_desc': payment_response.get('transaction_desc')
            }, 201


        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to process order: {str(e)}'}, 500


# Callback URL handler to update payment status

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback changes if there's a database error
            logging.error(f'Database error: {e}')
            return {'error': 'An error occurred while processing the order'}, 500



@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

    if not data:
        logging.error("No data received in callback")
        return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
    
    # Validate secret key (example)
    secret_key = request.headers.get('X-Callback-Secret')
    if secret_key != CALLBACK_SECRET:
        logging.error("Invalid callback secret")
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback secret"}), 403

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
        if result_code == 0:
            payment.status = 'complete'
            payment.transaction_desc = result_desc
        else:
            payment.status = 'failed'
            payment.transaction_desc = result_desc

        db.session.commit()


    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


        
class ShippingResource(Resource):
    def get(self, user_id):
        # Fetch the shipping address for the user
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if not shipping_address:
            return {"error": "Shipping address not found"}, 404

        return shipping_address.to_dict(), 200

        logging.debug(f'Payment status updated to: {payment.status}')
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200
    else:
        logging.error(f'Payment record not found for CheckoutRequestID: {checkout_request_id}')
        return jsonify({"ResultCode": 1, "ResultDesc": "Payment record not found"}), 404
    


class AddToCartResource(Resource):
    @user_required 
    def post(self):
        data = request.get_json()


    def post(self):
        data = request.get_json()

        user_id = data.get('user_id')
        if not user_id:
            return {'error': 'User ID is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404


        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()

        artwork = Artwork.query.get(data['artwork_id'])
        if not artwork:
            return {'error': 'Artwork not found'}, 404

        quantity = data.get('quantity', 1)

        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork.id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                artwork_id=artwork.id,
                quantity=quantity,
                title=artwork.title,
                description=artwork.description,
                price=artwork.price,
                image=artwork.image
            )
            db.session.add(cart_item)

        address = data.get('address')
        city = data.get('city')
        country = data.get('country')
        phone = data.get('phone')
        full_name = data.get('full_name')
        email = data.get('email')

        if not all([address, city, country, phone, full_name, email]):
            return {'error': 'All fields are required'}, 400

        # Check if a shipping address already exists for the user
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if shipping_address:
            return {'error': 'Shipping address already exists for this user'}, 400

        new_address = ShippingAddress(
            user_id=user_id,
            address=address,
            city=city,
            country=country,
            phone=phone,
            full_name=full_name,
            email=email
        )


        db.session.add(new_address)
        db.session.commit()

        return {'message': 'Shipping address created successfully', 'address': new_address.to_dict()}, 201


class RemoveFromCartResource(Resource):
    @user_required  # Ensure the user is authenticated
    def post(self):
        data = request.get_json()

        user_id = data.get('user_id')
        artwork_id = data.get('artwork_id')
        if not user_id or not artwork_id:
            return {'error': 'User ID and artwork ID are required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            return {'error': 'Cart not found'}, 404

        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
        if not cart_item:
            return {'error': 'Artwork not found in cart'}, 404
            return {'error': 'Artwork not found in cart'}, 404

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        db.session.commit()

        return {'message': 'Artwork removed from cart'}, 200

class ViewCartResource(Resource):
    @user_required
    def get(self, user_id):
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return {"error": "Cart not found"}, 404

        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return {"message": "Cart is empty"}, 200

        cart_items_list = [item.to_dict() for item in cart_items]

        return {'items': cart_items_list}, 200
    


from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.ticket import TicketResource
from Resources.ticket import MpesaCallbackResource
from Resources.ticket import CheckoutResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource
    
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(UserResource, '/user')
api.add_resource(AdminResource, '/admin')
api.add_resource(EventsResource, '/events', '/events/<int:id>')
api.add_resource(TicketResource, '/tickets', '/tickets/<int:id>')
api.add_resource(MpesaCallbackResource, '/callback')

    def put(self, user_id):
        data = request.get_json()
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if not shipping_address:
            return {'error': 'Shipping address not found'}, 404

        address = data.get('address', shipping_address.address)
        city = data.get('city', shipping_address.city)
        country = data.get('country', shipping_address.country)
        phone = data.get('phone', shipping_address.phone)
        full_name = data.get('full_name', shipping_address.full_name)
        email = data.get('email', shipping_address.email)

        shipping_address.address = address
        shipping_address.city = city
        shipping_address.country = country
        shipping_address.phone = phone
        shipping_address.full_name = full_name
        shipping_address.email = email

        db.session.commit()

        return {'message': 'Shipping address updated successfully', 'address': shipping_address.to_dict()}, 200        
        

api.add_resource(CheckoutResource, '/checkout')
api.add_resource(AddToCartResource, '/add_to_cart')
api.add_resource(RemoveFromCartResource, '/remove_from_cart')

api.add_resource(ViewCartResource, '/view_cart/<int:user_id>')
api.add_resource(ShippingResource, '/shipping_address', '/shipping_address/<int:user_id>')

api.add_resource(ViewCartResource,'/view_cart/<int:user_id>')
api.add_resource(CheckoutResource, '/checkout')
api.add_resource(BookingResource, '/bookings', '/bookings/<int:id>')
api.add_resource(TicketAdminResource, '/admin/tickets', '/admin/tickets/<int:id>')
api.add_resource(ArtworkListResource, '/artworks')
api.add_resource(ArtworkResource, '/artworks/<int:id>')
api.add_resource(AddToCartResource, '/cart/add')
api.add_resource(RemoveFromCartResource, '/cart/remove')
api.add_resource(ViewCartResource, '/cart/<int:user_id>')

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# Ensure no duplicate resources are added
api.add_resource(Home, '/')

if __name__ == '__main__':
    app.run(debug=True)



