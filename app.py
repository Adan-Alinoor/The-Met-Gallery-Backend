import base64
from datetime import datetime
import os
from flask import Flask, request, jsonify
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from models import db,User, Cart, CartItem, Order, Payment, OrderItem, Artwork
import logging
from flask_cors import CORS
import bcrypt

from auth import user_required, admin_required



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
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


        
class Home(Resource):
    def get(self):
        response_dict = {"message": "Welcome to The Met Gallery"}
        return jsonify(response_dict)

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

        # Create a new Payment record with a pending status
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


@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    # Log the incoming callback data for debugging
    logging.debug(f'Callback Data: {data}')

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
        logging.debug(f'Payment record found: {payment.id}')
        if result_code == 0:
            payment.status = 'completed'
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
    


class AddToCartResource(Resource):
    @user_required 
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

        db.session.commit()

        return {'message': 'Artwork added to cart'}, 201

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

