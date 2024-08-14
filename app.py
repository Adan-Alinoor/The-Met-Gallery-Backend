from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource,reqparse
from flask_migrate import Migrate
from models import db, User, Cart, CartItem, Order, Payment, OrderItem, Artwork, ShippingAddress, Message, Notification, Event, UserActivity, Booking
import bcrypt
import base64
from datetime import datetime,timedelta
from marshmallow import Schema, fields
from flask_jwt_extended import decode_token
from flask_marshmallow import Marshmallow

import os
from flask import Flask, request, jsonify
import requests

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from flask_cors import CORS
import logging
from sqlalchemy.exc import SQLAlchemyError
from auth import user_required, admin_required
from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.ticket import MpesaCallbackResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource

from flask_socketio import SocketIO, send, emit




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("EXTERNAL_DATABASE_URL")
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)
CALLBACK_SECRET = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

ma = Marshmallow(app)

migrate = Migrate(app, db)
db.init_app(app) 
jwt = JWTManager(app)
api = Api(app)
CORS(app)

class Signup(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        users = User.query.all()
        users_list = [user.to_dict() for user in users]
        return make_response({"count": len(users_list), "users": users_list}, 200)

    def post(self):
        email = User.query.filter_by(email=request.json.get('email')).first()
        if email:
            return make_response({"message": "Email already taken"}, 422)

        # Fetch the role and is_admin values from the request
        role = request.json.get("role", "user")
        is_admin = request.json.get("is_admin", False)

        # If is_admin is True, override the role to 'admin'
        if is_admin:
            role = "admin"

        new_user = User(
            username=request.json.get("username"),
            email=request.json.get("email"),
            password=generate_password_hash(request.json.get("password")),
            role=role,
            is_admin=is_admin
        )

        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=new_user.id)
        return make_response({
            "user": new_user.to_dict(),
            "access_token": access_token,
            "success": True,
            "message": "User has been created successfully"
        }, 201)

class Login(Resource):
    def post(self):
        email = request.json.get('email')
        password = request.json.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id)
            return make_response({
                "user": user.to_dict(),
                "is_admin": user.is_admin,
                "access_token": access_token,
                "success": True,
                "message": "Login successful"
            }, 200)
        return make_response({"message": "Invalid credentials"}, 401)
    
class VerifyToken(Resource):
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user:
            return make_response({
                "user": user.to_dict(),
                "success": True,
                "message": "Token is valid"
            }, 200)
        return make_response({"message": "Invalid token"}, 401)    


class Logout(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return {'message': f"{user.role.capitalize()} logged out successfully"}, 200

class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    bio = fields.Str(allow_none=True)
    profilePicture = fields.Url(required=False, missing='https://i.pinimg.com/564x/91/c9/60/91c960ce7fcd5d246597adbc5118bba4.jpg')

def decode_token_and_get_user_id(token):
    try:
        if isinstance(token, str):
            token = token.encode('utf-8')
        
        decoded_token = decode_token(token)
        print("Decoded Token:", decoded_token)
        
        user_id = decoded_token.get('sub')
        if user_id:
            return user_id
        else:
            print("Token does not contain 'sub' field")
            return None

    except Exception as e:
        print(f"Token decoding failed: {e}")
        return None

class UserRetrieval:
    @staticmethod
    def get_user_from_token(token):
        user_id = decode_token_and_get_user_id(token)
        print("User ID from Token:", user_id)
        if not user_id:
            return None
        
        user = User.query.get(user_id)
        print("User from Database:", user)
        if user:
            return {
                "name": user.name,
                "email": user.email,
                "bio": user.bio or None,
                "profilePicture": user.profile_picture or 'https://i.pinimg.com/564x/91/c9/60/91c960ce7fcd5d246597adbc5118bba4.jpg'
            }
        return None

class UserProfile(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        print("Current User ID:", current_user)

        if not current_user:
            return {"message": "Invalid token or user not found"}, 401

        user = UserRetrieval.get_user_from_token(current_user)
        if user is None:
            return {"message": "User not found"}, 404

        user_schema = UserSchema()
        return user_schema.dump(user)


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

class UsersResource(Resource):
    @jwt_required()
    def get(self):      
        # Query all users
        users = User.query.all()
        
        # Return user data
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at
        } for user in users])


class ArtworkListResource(Resource):
    @jwt_required()
    def get(self):
        try:
            artworks = Artwork.query.all()
            return [artwork.to_dict() for artwork in artworks], 200
        except Exception as e:
            return {"error": str(e)}, 500

    @user_required  
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
            artwork = Artwork.query.get(id)
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

    @user_required  
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
            return {'error': 'artwork not found'}, 404

        
        quantity = data.get('quantity', 1)  
        
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork.id).first()
        if cart_item:
            
            cart_item.quantity += quantity  
        else:
            
            cart_item = CartItem(
                cart_id=cart.id,
                artwork_id=artwork.id,
                quantity=quantity, 
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

       
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        db.session.commit()

        return {'message': 'Artwork removed from cart'}, 200


class ViewCartResource(Resource):
    def get(self, user_id):
       
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return {"error": "Cart not found"}, 404

        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return {"message": "Cart is empty"}, 200

        
        cart_items_list = [item.to_dict() for item in cart_items]
        return {'items': cart_items_list}, 200




class Home(Resource):
    def get(self):
        response_dict = {"message": "Welcome to The Met Gallery"}
        return jsonify(response_dict)


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
        "CallBackURL": "https://5769-102-214-74-3.ngrok-free.app/callback",  
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
class ArtworkCheckoutResource(Resource):
    @staticmethod
    def initiate_mpesa_payment(payment_data):
        
        if not isinstance(payment_data, dict):
            logging.error(f'Expected a dictionary but got: {type(payment_data)}')
            return {'error': 'Invalid payment data format'}, 400

        logging.debug(f'Payment data: {payment_data}')
        
      
        user_id = payment_data.get('user_id')
        order_id = payment_data.get('order_id')
        phone_number = payment_data.get('phone_number')
        amount = payment_data.get('amount')
        
      
        if not all([user_id, order_id, phone_number, amount]):
            logging.error('Missing required fields in payment data')
            return {'error': 'Missing required fields'}, 400


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
            transaction_id=None, 
            status='pending',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(payment)
        db.session.commit()

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
            "CallBackURL": "https://fcbf-102-214-74-3.ngrok-free.app",  
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

            if response_data.get('ResponseCode') == '0':
                payment.transaction_id = response_data.get('CheckoutRequestID')
                payment.status = 'initiated'
                payment.transaction_desc = "Payment initiated successfully"
                db.session.commit()
                return {'message': 'Payment initiated successfully', 'transaction_desc': payment.transaction_desc}, 201
            else:
                payment.status = 'failed'
                payment.transaction_desc = response_data.get('Description', 'Payment failed')
                db.session.commit()
                return {'error': 'Failed to initiate payment'}, 400

        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling M-Pesa API: {e}')
            payment.status = 'failed'
            payment.transaction_desc = 'Failed to connect to M-Pesa API'
            db.session.commit()
            return {'error': 'Failed to connect to M-Pesa API'}, 500
        except ValueError:
            logging.error(f'Invalid JSON response: {response.text}')
            payment.status = 'failed'
            payment.transaction_desc = 'Invalid response from M-Pesa API'
            db.session.commit()
            return {'error': 'Invalid response from M-Pesa API'}, 500

    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
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

            payment_response, status_code = self.initiate_mpesa_payment(payment_data)

            if status_code != 201:
                db.session.rollback()
                return payment_response, 400

            return {
                'message': 'Order created and payment initiated successfully',
                'order_id': order.id,
                'transaction_desc': payment_response.get('transaction_desc')
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Database error: {e}')
            return {'error': 'An error occurred while processing the order'}, 500


# @app.route('/callback', methods=['POST'])
# def mpesa_callback():
#     data = request.get_json()

#     checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
#     result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
#     result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

#     if not data:
#         logging.error("No data received in callback")
#         return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
    
#     secret_key = request.headers.get('X-Callback-Secret')
#     if secret_key != CALLBACK_SECRET:
#         logging.error("Invalid callback secret")
#         return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback secret"}), 403

#     try:
#         stk_callback = data['Body']['stkCallback']
#         checkout_request_id = stk_callback['CheckoutRequestID']
#         result_code = stk_callback['ResultCode']
#         result_desc = stk_callback['ResultDesc']
#     except KeyError as e:
#         logging.error(f'Missing key in callback data: {e}')
#         return jsonify({"ResultCode": 1, "ResultDesc": "Invalid data format"}), 400

#     # Log the extracted callback data
#     logging.debug(f'CheckoutRequestID: {checkout_request_id}')
#     logging.debug(f'ResultCode: {result_code}')
#     logging.debug(f'ResultDesc: {result_desc}')

#     payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()

#     if payment:
#         if result_code == 0:
#             payment.status = 'complete'
#             payment.transaction_desc = result_desc
#         else:
#             payment.status = 'failed'
#             payment.transaction_desc = result_desc

#         db.session.commit()


#     return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


        
class ShippingResource(Resource):
    @user_required
    def get(self, user_id):
      
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if not shipping_address:
            return {"error": "Shipping address not found"}, 404

        return shipping_address.to_dict(), 200

    @user_required
    def post(self):
        data = request.get_json()

        user_id = data.get('user_id')
        address = data.get('address')
        city = data.get('city')
        country = data.get('country')
        phone = data.get('phone')
        full_name = data.get('full_name')
        email = data.get('email')

        if not all([user_id, address, city, country, phone, full_name, email]):
            return {'error': 'All fields are required'}, 400

       
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

    @user_required
    def put(self, user_id):
        data = request.get_json()
        shipping_address = ShippingAddress.query.filter_by(user_id=user_id).first()
        if not shipping_address:
            return {'error': 'Shipping address not found'}, 404

        shipping_address.address = data.get('address', shipping_address.address)
        shipping_address.city = data.get('city', shipping_address.city)
        shipping_address.country = data.get('country', shipping_address.country)
        shipping_address.phone = data.get('phone', shipping_address.phone)
        shipping_address.full_name = data.get('full_name', shipping_address.full_name)
        shipping_address.email = data.get('email', shipping_address.email)

        db.session.commit()

        return {'message': 'Shipping address updated successfully', 'address': shipping_address.to_dict()}, 200


class AddToCartResource(Resource):
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
            return {'error': 'artwork not found'}, 404

        
        quantity = data.get('quantity', 1)  
        
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork.id).first()
        if cart_item:
            cart_item.quantity += quantity  
        else:
            
            cart_item = CartItem(
                cart_id=cart.id,
                artwork_id=artwork.id,
                quantity=quantity, 
                title = artwork.title,
                description=artwork.description,
                price=artwork.price,
                image=artwork.image
            )
            db.session.add(cart_item)

        db.session.commit()

        return {'message': 'Artwork added to cart'}, 201

class RemoveFromCartResource(Resource):
    @user_required  
    def delete(self):
        data = request.get_json()
        
        # Extract user_id and artwork_id from the request data
        user_id = data.get('user_id')
        artwork_id = data.get('artwork_id')

        # Check if user_id and artwork_id are provided
        if not user_id or not artwork_id:
            return {'error': 'User ID and artwork ID are required'}, 400

        # Retrieve the user by user_id
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find the cart associated with the user
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            return {'error': 'Cart not found'}, 404

        # Find the cart item that matches the given artwork_id
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
        if not cart_item:
            return {'error': 'Artwork not found in cart'}, 404

        # Remove the cart item if its quantity is 1; otherwise, reduce the quantity
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        # Commit the changes to the database
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
    
@app.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    data = request.json
    recipient_id = data.get('recipient_id')
    message_text = data.get('message')
    sender_id = get_jwt_identity()

    if not recipient_id or not message_text:
        return jsonify({"error": "Invalid data"}), 400

    new_message = Message(sender_id=sender_id, recipient_id=recipient_id, content=message_text)
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('new_message', {
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'content': message_text,
        'sent_at': new_message.sent_at.isoformat()
    })

    return jsonify({
        'id': new_message.id,
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'content': message_text,
        'sent_at': new_message.sent_at.isoformat()
    }), 201

@app.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    user_id = get_jwt_identity()
    messages = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).all()

    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'recipient_id': msg.recipient_id,
        'content': msg.content,
        'sent_at': msg.sent_at.isoformat()
    } for msg in messages])

@socketio.on('message')
def handle_message(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


class DashboardOverviewResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()

        bookings = Booking.query.filter_by(user_id=current_user_id).all()
        notifications = Notification.query.filter_by(user_id=current_user_id).all()
        user_activities = UserActivity.query.filter_by(user_id=current_user_id).all()
        events = Event.query.all()

        booking_data = [{
            'id': booking.id,
            'user_id': booking.user_id,
            'event_id': booking.event_id,
            'booking_date': booking.created_at.isoformat()
        } for booking in bookings]

        notification_data = [{
            'id': notification.id,
            'user_id': notification.user_id,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat()
        } for notification in notifications]

        event_data = [{
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat()
        } for event in events]

        user_activity_data = [{
            'id': activity.id,
            'user_id': activity.user_id,
            'activity_type': activity.activity_type,
            'timestamp': activity.timestamp.isoformat()
        } for activity in user_activities]

        response = {
            'bookings': booking_data,
            'notifications': notification_data,
            'events': event_data,
            'user_activities': user_activity_data
        }

        return jsonify(response)


from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.ticket import TicketResource
from Resources.ticket import MpesaCallbackResource
from Resources.ticket import EventCheckoutResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource
    
# api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(UserResource, '/user')
api.add_resource(UserProfile, '/userprofile')
api.add_resource(AdminResource, '/admin')
api.add_resource(EventsResource, '/events', '/events/<int:id>')
api.add_resource(TicketResource, '/tickets', '/tickets/<int:id>')
api.add_resource(MpesaCallbackResource, '/callback')
api.add_resource(AddToCartResource, '/add_to_cart')
# api.add_resource(RemoveFromCartResource, '/remove_from_cart')
api.add_resource(RemoveFromCartResource, '/remove_from_cart')

api.add_resource(ViewCartResource, '/view_cart/<int:user_id>')
api.add_resource(ShippingResource, '/shipping_address', '/shipping_address/<int:user_id>')
api.add_resource(EventCheckoutResource, '/eventcheckout')
api.add_resource(ArtworkCheckoutResource, '/artworkcheckout')
api.add_resource(BookingResource, '/bookings', '/bookings/<int:id>')
api.add_resource(TicketAdminResource, '/admin/tickets', '/admin/tickets/<int:id>')
api.add_resource(ArtworkListResource, '/artworks')
api.add_resource(ArtworkResource, '/artworks/<int:id>')
api.add_resource(DashboardOverviewResource, '/dashboard')
api.add_resource(Home, '/')
api.add_resource(UsersResource, '/users')
api.add_resource(Signup, '/signup')
# api.add_resource(Login, '/login')
api.add_resource(VerifyToken, '/verify-token')

logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5555)

