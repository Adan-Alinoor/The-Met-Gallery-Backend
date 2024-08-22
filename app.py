import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, make_response, session
from flask_restful import Api, Resource,reqparse
from flask_migrate import Migrate
from models import db, User, Cart, CartItem, Order, Payment, OrderItem, Artwork, Message, Notification, Event, UserActivity, Booking
import bcrypt
import base64
from datetime import datetime,timedelta
from marshmallow import Schema, fields
from flask_marshmallow import Marshmallow

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

import os
from flask import Flask, request, jsonify
import requests
import uuid

from flask_sqlalchemy import SQLAlchemy
from jwt.exceptions import ExpiredSignatureError
from flask_migrate import Migrate

from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token, verify_jwt_in_request,get_jwt
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
# from socketio import ASGIApp, Server

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("EXTERNAL_DATABASE_URL")
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)
CALLBACK_SECRET = 'your_secret_key_here'



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'zizkoteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'xuog xbgx togb uspq'
app.config['MAIL_DEFAULT_SENDER'] = 'zizkoteam@gmail.com'

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
# sio = Server(cors_allowed_origins=["https://the-met-gallery-frontend-nbi7.vercel.app"])
# app.mount("/", ASGIApp(sio, other_asgi_app=app))
socketio = SocketIO(app, cors_allowed_origins=["https://the-met-gallery-frontend-wh3n.vercel.app"], async_mode='eventlet')


ma = Marshmallow(app)

migrate = Migrate(app, db)
db.init_app(app) 
jwt = JWTManager(app)
api = Api(app)
CORS(app)



class Signup(Resource):
    def post(self):
        data = request.json

        # Check if email already exists
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return make_response({"message": "Email already taken"}, 422)

        try:
            # Create new user
            new_user = User(
                username=data.get('username'),
                email=data.get('email'),
                password=generate_password_hash(data.get('password')),
                role=data.get('role', 'user'),
                is_admin=data.get('is_admin', False),
                email_confirmed=False  # Set email_confirmed to False initially
            )

            # Add new user to the database
            db.session.add(new_user)
            db.session.commit()

            # Generate email confirmation token
            token = s.dumps(new_user.email, salt='email-confirmation')
            verify_url = f"https://the-met-gallery-backend.onrender.com/verify/{token}"

            # Prepare confirmation email
            msg = Message("Please confirm your email", recipients=[new_user.email])
            msg.body = f"Thanks for signing up! Please confirm your email by clicking on the link: {verify_url}"

            # Send confirmation email
            try:
                mail.send(msg)
                logging.info(f"Email sent successfully to {new_user.email} with token {token}")
            except Exception as e:
                logging.error(f"Failed to send email: {e}")
                db.session.rollback()  # Rollback the transaction if email fails
                return make_response({"message": "Error sending confirmation email. Please try again later."}, 500)

            return make_response({
                "message": "User has been created successfully, please check your email to verify your account."
            }, 201)

        except Exception as e:
            db.session.rollback()  # Rollback in case of any errors
            logging.error(f"Error during registration: {e}")
            return make_response({"message": "Error during registration. Please try again later."}, 500)

class VerifyEmail(Resource):
    def get(self, token):
        try:
            email = s.loads(token, salt='email-confirmation', max_age=3600)  # Token expires after 1 hour
        except SignatureExpired:
            logging.warning("Verification token expired.")
            return make_response({"message": "The token has expired. Please request a new verification email."}, 400)
        except BadSignature:
            logging.warning("Invalid verification token.")
            return make_response({"message": "Invalid token. Please request a new verification email."}, 400)

        user = User.query.filter_by(email=email).first()
        if user is None:
            logging.warning(f"User with email {email} not found.")
            return make_response({"message": "User not found."}, 404)

        if user.email_confirmed:
            return make_response({"message": "Account already verified."}, 200)

        user.email_confirmed = True
        db.session.commit()

        logging.info(f"User with email {email} has been successfully verified.")
        return make_response({"message": "Your account has been verified. You can now log in."}, 200)
    

class TestEmail(Resource):
    def get(self):
        try:
            # Create a test email message
            msg = Message("Test Email", recipients=["your_email@example.com"])
            msg.body = "This is a test email."
            # Send the email
            mail.send(msg)
            return make_response("Email sent successfully!", 200)
        except Exception as e:
            print(f"Error sending email: {e}")
            return "Failed to send email."
            
                

class Login(Resource):
    def post(self):
        # Get email and password from the request
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Query for the user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if the user exists and if the password is correct
        if not user or not check_password_hash(user.password, password):
            return make_response({"message": "Invalid email or password."}, 401)

        # Check if the user is verified
        if not user.email_confirmed:  # Updated field
            return make_response({"message": "Please verify your email before logging in."}, 403)

        # Generate an access token
        access_token = create_access_token(identity=user.id)
        
        # Return a success response with user data and token
        return make_response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin
            },
            "access_token": access_token,
            "success": True,
            "message": "Login successful"
        }, 200)


    
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

    def get(self):
        try:
            artworks = Artwork.query.all()
            return [artwork.to_dict() for artwork in artworks], 200
        except Exception as e:
            return {"error": str(e)}, 500
        
    @jwt_required()
    def post(self, user_id):
        data = request.get_json()
        print("Received data:", data)
        if not data:
            return {"error": "No input data provided"}, 400
        if not all(k in data for k in ("title", "description", "price", "image")):
            return {"error": "Missing fields in input data"}, 400

        try:
            new_artwork = Artwork(
                title=data['title'],
                description=data['description'],
                price=data['price'],
                image=data['image'],
                user_id=user_id  # Linking the artwork to the user
            )
            db.session.add(new_artwork)
            db.session.commit()
            return {"message": "Artwork created", "artwork": new_artwork.to_dict()}, 201
        except Exception as e:
            print("Error creating artwork:", str(e))
            return {"error": str(e)}, 500

class ArtworkResource(Resource):
   
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
        
class ArtworkByOrderResource(Resource):
    @user_required  
    def get(self, order_id):
        try:
            order = Order.query.get(order_id)
            if order is None:
                return {"error": "Order not found"}, 404
            artworks = []
            for item in order.items:
                artwork = item.artwork
                artworks.append(artwork.to_dict())
            return artworks, 200
        except Exception as e:
            return {"error": str(e)}, 500

class AddToCartResource(Resource):
    def post(self):
        verify_jwt_in_request(optional=True)
        
        # Get the current user ID if logged in
        current_user_id = get_jwt_identity()

        if current_user_id:
            # If the user is logged in, find or create an active cart for the user
            active_cart = Cart.query.filter_by(user_id=current_user_id, is_active=True).first()
            if not active_cart:
                active_cart = Cart(user_id=current_user_id, is_active=True)
                db.session.add(active_cart)
                db.session.commit()
        else:
            # If the user is not logged in, use a session key
            sess = request.cookies.get('session_key')
            if not sess:
                # Generate a session key if not already present
                session_key = str(uuid.uuid4())
                response = make_response()
                response.set_cookie('session_key', session_key)

            # Find or create an active cart for the session
            active_cart = Cart.query.filter_by(sess=sess, is_active=True).first()
            if not active_cart:
                active_cart = Cart(sess=sess, is_active=True)
                db.session.add(active_cart)
                db.session.commit()

        # Extract the artwork_id and quantity from the post data
        data = request.get_json()
        artwork_id = data.get('artwork_id')
        quantity = data.get('quantity', 1)

        # Fetch artwork price from the database
        artwork = Artwork.query.get(artwork_id)
        if not artwork:
            return {'error': 'Artwork not found'}, 404

        price = artwork.price
        if price is None:
            return {'error': 'Price not set for this artwork'}, 400

        # Check if the item already exists in the cart
        cart_item = CartItem.query.filter_by(cart_id=active_cart.id, artwork_id=artwork_id).first()
        if cart_item:
            # If it exists, update the quantity
            cart_item.quantity += quantity
        else:
            # If it doesn't exist, create a new cart item with price
            cart_item = CartItem(
                cart_id=active_cart.id,
                artwork_id=artwork_id,
                quantity=quantity,
                price=price
            )
            db.session.add(cart_item)

        db.session.commit()

        return {"message": "Item added to cart successfully", "cart_id": active_cart.id}, 200



# class AddToCartResource(Resource):
#     def post(self):
#         verify_jwt_in_request(optional=True)
#         # Get the current user ID if logged in
#         current_user_id = get_jwt_identity()

#         if current_user_id:
#             # If the user is logged in, find or create an active cart for the user
#             active_cart = Cart.query.filter_by(user_id=current_user_id, is_active=True).first()
#             if not active_cart:
#                 active_cart = Cart(user_id=current_user_id, is_active=True)
#                 db.session.add(active_cart)
#                 db.session.commit()
#         else:
#             # If the user is not logged in, use a session key
#             sess = request.cookies.get('session_key')
#             if not sess:
#                 # Generate a session key if not already present
#                 session_key = str(uuid.uuid4())
#                 response = make_response()
#                 response.set_cookie('session_key', session_key)
#                 response.headers['Content-Type'] = 'application/json'  # Ensure the response is JSON
#                 return response

#             # Find or create an active cart for the session
#             active_cart = Cart.query.filter_by(sess=sess, is_active=True).first()
#             if not active_cart:
#                 active_cart = Cart(sess=sess, is_active=True)
#                 db.session.add(active_cart)
#                 db.session.commit()

#         # Extract the artwork_id and quantity from the post data
#         data = request.get_json()
#         artwork_id = data.get('artwork_id')
#         quantity = data.get('quantity', 1)

#         # Use the helper function to add the item to the cart, including the price
#         result = add_to_cart(active_cart, artwork_id, quantity)

#         if 'error' in result:
#             return result, 404

#         return {"message": "Item added to cart successfully", "cart_id": active_cart.id}, 200


# def add_to_cart(cart, artwork_id, quantity):
#     artwork = Artwork.query.get(artwork_id)
#     if not artwork:
#         return {'error': 'Artwork not found'}, 404

#     cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
#     if cart_item:
#         cart_item.quantity += quantity
#     else:
#         cart_item = CartItem(
#             cart_id=cart.id,
#             artwork_id=artwork_id,
#             quantity=quantity,
#             price=artwork.price
#         )
#         db.session.add(cart_item)

#     db.session.commit()
#     return {'message': 'Item added to cart'}, 201




     
class UpdateCartItemResource(Resource):
    def put(self, item_id):
        verify_jwt_in_request(optional=True)
        # Get the current user ID if logged in, or session key if not
        current_user = get_jwt_identity()
        session_key = request.cookies.get('session')

        # Fetch the active cart based on user or session key
        cart_query = Cart.query.filter_by(is_active=True)
        
        if current_user:
            cart_query = cart_query.filter_by(user_id=current_user)
        else:
            cart_query = cart_query.filter_by(sess=session_key)
        
        cart = cart_query.first()
        
        print("we starting")

        if not cart:
            return {"error": "Active cart not found"}, 404
        
        data = request.get_json()
        new_quantity = data.get('quantity')

        # Fetch the CartItem by id
        cart_item = CartItem.query.filter_by(artwork_id=item_id, cart_id=cart.id).first()
        if not cart_item:
            return {"error": "Cart item not found"}, 404
        if new_quantity is None or new_quantity <= 0:
            return {"error": "Invalid quantity"}, 400

        # Update the CartItem's quantity
        cart_item.quantity = new_quantity
        db.session.commit()
        # Fetch all items related to the active cart
        all_cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        serialized_items = [item.to_dict() for item in all_cart_items]

        return {
            "message": "Cart item updated successfully",
            "cart_items": serialized_items
        }, 200


class RemoveFromCartResource(Resource):
    def delete(self, item_id):
        verify_jwt_in_request(optional=True)
        # Get the current user ID if logged in, or session key if not
        current_user = get_jwt_identity()
        session_key = request.cookies.get('session')

        # Fetch the active cart based on user or session key
        cart_query = Cart.query.filter_by(is_active=True)
        
        if current_user:
            cart_query = cart_query.filter_by(user_id=current_user)
        else:
            cart_query = cart_query.filter_by(sess=session_key)
        
        cart = cart_query.first()

        if not cart:
            return {"error": "Active cart not found"}, 404

        # Fetch the CartItem by id
        cart_item = CartItem.query.filter_by(artwork_id=item_id, cart_id=cart.id).first()

        if not cart_item:
            return {"error": "Cart item not found"}, 404

        # Delete the CartItem from the database
        db.session.delete(cart_item)
        db.session.commit()

        # Fetch all remaining items related to the active cart
        all_cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        serialized_items = [item.to_dict() for item in all_cart_items]

        return {
            "message": "Cart item deleted successfully",
            "cart_items": serialized_items
        }, 200


class ViewCartResource(Resource):
    def get(self):
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        session_key = request.cookies.get('session')

        # Fetch the active cart based on user or session key
        cart_query = Cart.query.filter_by(is_active=True)
        
        if current_user:
            cart_query = cart_query.filter_by(user_id=current_user)
        else:
            cart_query = cart_query.filter_by(sess=session_key)
        
        cart = cart_query.first()

        if not cart:
            return {"error": "Active cart not found"}, 404
        
        # Fetch all remaining items related to the active cart
        all_cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        serialized_items = [item.to_dict() for item in all_cart_items]
        

        return {
            "message": "Cart fetched successfully",
            "cart_items": serialized_items
        }, 200

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
    
    
    m
    

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
        "CallBackURL": "  https://1a61-102-214-72-2.ngrok-free.app /callback",  
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

            selected_items = data.get('items', [])
            if not selected_items:
                return {'error': 'No items selected for checkout'}, 400

            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            cart = Cart.query.filter_by(user_id=user.id, is_active=True).first()
            if not cart or not cart.items:
                return {'error': 'Cart is empty'}, 400

            total_amount = 0
            for selected_item in selected_items:
                artwork_id = selected_item.get('artwork_id')
                quantity = selected_item.get('quantity', 1)

                cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
                if not cart_item or cart_item.quantity < quantity:
                    return {'error': f'Invalid quantity for artwork ID {artwork_id}'}, 400
                
                if cart_item.price is None:
                    return {'error': f'Price not set for artwork ID {artwork_id}'}, 400
                
                total_amount += cart_item.price * quantity

            # Create the order with the total amount
            order = Order(user_id=user.id, total_price=total_amount)
            db.session.add(order)
            db.session.flush()  # Ensure the order.id is available

            for selected_item in selected_items:
                artwork_id = selected_item.get('artwork_id')
                quantity = selected_item.get('quantity', 1)

                cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()

                if cart_item:
                    order_item = OrderItem(
                        order_id=order.id,
                        artwork_id=artwork_id,
                        quantity=quantity,
                        price=cart_item.price,
                    )
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



# class ArtworkCheckoutResource(Resource):
#     @staticmethod
#     def initiate_mpesa_payment(payment_data):
#         if not isinstance(payment_data, dict):
#             logging.error(f'Expected a dictionary but got: {type(payment_data)}')
#             return {'error': 'Invalid payment data format'}, 400

#         logging.debug(f'Payment data: {payment_data}')

#         user_id = payment_data.get('user_id')
#         order_id = payment_data.get('order_id')
#         phone_number = payment_data.get('phone_number')
#         amount = payment_data.get('amount')

#         if not all([user_id, order_id, phone_number, amount]):
#             logging.error('Missing required fields in payment data')
#             return {'error': 'Missing required fields'}, 400

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         order = Order.query.get(order_id)
#         if not order:
#             return {'error': 'Order not found'}, 404

#         payment = Payment(
#             user_id=user.id,
#             order_id=order.id,
#             amount=amount,
#             phone_number=phone_number,
#             transaction_id=None, 
#             status='pending',
#             created_at=datetime.now(),
#             updated_at=datetime.now()
#         )
#         db.session.add(payment)
#         db.session.commit()

#         access_token = get_mpesa_access_token()
#         headers = {
#             'Authorization': f'Bearer {access_token}',
#             'Content-Type': 'application/json'
#         }
#         password, timestamp = generate_password(SHORTCODE, LIPA_NA_MPESA_ONLINE_PASSKEY)
#         payload = {
#             "BusinessShortCode": SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": amount,
#             "PartyA": phone_number,
#             "PartyB": SHORTCODE,
#             "PhoneNumber": phone_number,
#             "CallBackURL": "https://e9b4-102-214-72-2.ngrok-free.app/callback ",  
#             "AccountReference": f"Order{order.id}",
#             "TransactionDesc": "Payment for order"
#         }

#         try:
#             response = requests.post(
#                 "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
#                 headers=headers,
#                 json=payload
#             )

#             logging.debug(f'M-Pesa API Response: {response.text}')
#             response_data = response.json()

#             if response_data.get('ResponseCode') == '0':
#                 payment.transaction_id = response_data.get('CheckoutRequestID')
#                 payment.status = 'initiated'
#                 payment.transaction_desc = "Payment initiated successfully"
#                 db.session.commit()
#                 return {'message': 'Payment initiated successfully', 'transaction_desc': payment.transaction_desc}, 201
#             else:
#                 payment.status = 'failed'
#                 payment.transaction_desc = response_data.get('Description', 'Payment failed')
#                 db.session.commit()
#                 return {'error': 'Failed to initiate payment'}, 400

#         except requests.exceptions.RequestException as e:
#             logging.error(f'Error calling M-Pesa API: {e}')
#             payment.status = 'failed'
#             payment.transaction_desc = 'Failed to connect to M-Pesa API'
#             db.session.commit()
#             return {'error': 'Failed to connect to M-Pesa API'}, 500
#         except ValueError:
#             logging.error(f'Invalid JSON response: {response.text}')
#             payment.status = 'failed'
#             payment.transaction_desc = 'Invalid response from M-Pesa API'
#             db.session.commit()
#             return {'error': 'Invalid response from M-Pesa API'}, 500

#     @jwt_required()
#     def post(self):
#         try:
#             user_id = get_jwt_identity()
#             if not user_id:
#                 return {'error': 'User ID is required'}, 400

#             data = request.get_json()
#             if not data:
#                 return {'error': 'No input data provided'}, 400

#             phone_number = data.get('phone_number')
#             if not phone_number:
#                 return {'error': 'Phone number is required'}, 400

#             selected_items = data.get('items', [])
#             if not selected_items:
#                 return {'error': 'No items selected for checkout'}, 400

#             user = User.query.get(user_id)
#             if not user:
#                 return {'error': 'User not found'}, 404

#             cart = Cart.query.filter_by(user_id=user.id).first()
#             if not cart or not cart.items:
#                 return {'error': 'Cart is empty'}, 400

#             total_amount = 0
#             for selected_item in selected_items:
#                 artwork_id = selected_item.get('artwork_id')
#                 quantity = selected_item.get('quantity', 1)

#                 cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
#                 if not cart_item or cart_item.quantity < quantity:
#                     return {'error': f'Invalid quantity for artwork ID {artwork_id}'}, 400

#                 total_amount += cart_item.price * quantity

#             # Create the order with the total amount
#             order = Order(user_id=user.id, total_price=total_amount)
#             db.session.add(order)
#             db.session.flush()  # Ensure the order.id is available

#             for selected_item in selected_items:
#                 artwork_id = selected_item.get('artwork_id')
#                 quantity = selected_item.get('quantity', 1)

#                 cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()

#                 order_item = OrderItem(
#                     order_id=order.id,
#                     artwork_id=artwork_id,
#                     quantity=quantity,
#                     price=cart_item.price,
#                     title=cart_item.title,  # Ensure title is passed here
#                     description=cart_item.description,  # Include other fields if necessary
#                     image=cart_item.image  # Include other fields if necessary
#                 )
#                 db.session.add(order_item)

#                 if cart_item.quantity > quantity:
#                     cart_item.quantity -= quantity
#                 else:
#                     db.session.delete(cart_item)

#             db.session.commit()

#             payment_data = {
#                 'user_id': user.id,
#                 'order_id': order.id,
#                 'phone_number': phone_number,
#                 'amount': total_amount
#             }

#             payment_response, status_code = self.initiate_mpesa_payment(payment_data)

#             if status_code != 201:
#                 db.session.rollback()
#                 return payment_response, 400

#             return {
#                 'message': 'Order created and payment initiated successfully',
#                 'order_id': order.id,
#                 'transaction_desc': payment_response.get('transaction_desc')
#             }, 201

#         except SQLAlchemyError as e:
#             db.session.rollback()
#             logging.error(f'Database error: {e}')
#             return {'error': 'An error occurred while processing the order'}, 500


@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

    if not data:
        logging.error("No data received in callback")
        return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
    
    secret_key = request.headers.get('X-Callback-Secret')
    if secret_key != CALLBACK_SECRET:
        logging.error("Invalid callback secret")
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback secret"}), 403

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

class MessageResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        messages = Message.query.filter(
            (Message.sender_id == user_id) | (Message.recipient_id == user_id)
        ).all()

        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'recipient_id': msg.recipient_id,
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat()
        } for msg in messages])

# Add the resource to the API with a URL


# SocketIO event handlers
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

        # Fetch data
        bookings = Booking.query.filter_by(user_id=current_user_id).all()
        notifications = Notification.query.filter_by(user_id=current_user_id).all()
        user_activities = UserActivity.query.filter_by(user_id=current_user_id).all()
        events = Event.query.filter_by(user_id=current_user_id).all()
        
        # Additional data
        artworks_count = Artwork.query.count()
        users_count = User.query.count()
        events_count = Event.query.count()

        # Recent transactions
        recent_transactions = Payment.query.order_by(Payment.created_at.desc()).all()

        # Prepare data for response
        event_dict = {event.id: {'title': event.title, 'image': event.image_url} for event in events}

        artPayments = Payment.query.join(Booking).filter(Booking.user_id == current_user_id).all()
        eventPayments = Payment.query.join(Order).filter(Order.user_id == current_user_id).all()

        booking_data = [{
            'id': booking.id,
            'user_id': booking.user_id,
            'event_id': booking.event_id,
            'event_title': event_dict.get(booking.event_id, {}).get('title', 'Unknown Event'),
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
            'image': event.image_url,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat()
        } for event in events]

        payment_data = {
            'art_payments': [{
                'id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'phone_number': payment.phone_number,
                'payment_type': payment.payment_type,
                'created_at': payment.created_at.isoformat()
            } for payment in artPayments],
            'event_payments': [{
                'id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'phone_number': payment.phone_number,
                'payment_type': payment.payment_type,
                'created_at': payment.created_at.isoformat()
            } for payment in eventPayments]
        }

        user_activity_data = [{
            'id': activity.id,
            'user_id': activity.user_id,
            'username': User.query.get(activity.user_id).username,  # Fetch username
            'activity_type': activity.activity_type,
            'description': activity.description,
            'timestamp': activity.timestamp.isoformat()
        } for activity in user_activities]

        # Format recent transactions
        recent_transactions_data = [{
            'id': transaction.id,
            'amount': transaction.amount,
            'status': transaction.status,
            'created_at': transaction.created_at.isoformat()
        } for transaction in recent_transactions]

        response = {
            'artworks_count': artworks_count,
            'events_count': events_count,
            'users_count': users_count,
            'recent_transactions': recent_transactions_data,
            'recent_activity': user_activity_data,
        }

        return jsonify(response)

    
from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.ticket import TicketResource
from Resources.ticket import MpesaCallbackResource
from Resources.ticket import EventCheckoutResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource
# from Resources.payment import PaymentSearchResource
from Resources.payment import PaymentResource

    
# api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(UserResource, '/user')
api.add_resource(UserProfile, '/userprofile')
api.add_resource(AdminResource, '/admin')
api.add_resource(EventsResource, '/events', '/events/<int:id>', '/events/<int:user_id>')
api.add_resource(TicketResource, '/tickets', '/tickets/<int:id>')
api.add_resource(MpesaCallbackResource, '/callback')
api.add_resource(AddToCartResource, '/add_to_cart')
api.add_resource(UpdateCartItemResource, '/update_cart_item/<int:item_id>')
api.add_resource(RemoveFromCartResource, '/remove_from_cart/<int:item_id>')

api.add_resource(MessageResource, '/messages')
api.add_resource(PaymentResource, '/payments')
# api.add_resource(PaymentSearchResource, '/payments/search')
api.add_resource(ArtworkByOrderResource, '/artworks/order/<int:order_id>')

api.add_resource(ViewCartResource, '/view_cart')
api.add_resource(EventCheckoutResource, '/eventcheckout')
api.add_resource(ArtworkCheckoutResource, '/artworkcheckout')
api.add_resource(BookingResource, '/bookings', '/bookings/<int:id>', '/bookings/<int:user_id>')
api.add_resource(TicketAdminResource, '/admin/tickets', '/admin/tickets/<int:id>')
api.add_resource(ArtworkListResource, '/artworks')
api.add_resource(ArtworkResource, '/artworks/<int:id>')
api.add_resource(DashboardOverviewResource, '/dashboard')
api.add_resource(Home, '/')
api.add_resource(UsersResource, '/users')
api.add_resource(Signup, '/signup')
# api.add_resource(Login, '/login')
api.add_resource(VerifyToken, '/verify-token')
api.add_resource(TestEmail, '/test-email')
api.add_resource(VerifyEmail, '/verify/<string:token>')

logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
