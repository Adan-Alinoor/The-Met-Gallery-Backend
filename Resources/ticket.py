# import base64
# import json
# import logging
# import os
# import threading
# import time
# from datetime import datetime
# from flask_jwt_extended import jwt_required
# import requests
# from dotenv import load_dotenv
# from flask import request, current_app,make_response,jsonify
# from flask_restful import Resource, reqparse
# from sqlalchemy.exc import SQLAlchemyError
# from models import db, Ticket, Booking, User, Payment

# load_dotenv()

# CONSUMER_KEY = os.getenv('CONSUMER_KEY')
# CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
# SHORTCODE = os.getenv('SHORTCODE')
# LIPA_NA_MPESA_ONLINE_PASSKEY = os.getenv('LIPA_NA_MPESA_ONLINE_PASSKEY')
# PHONE_NUMBER = os.getenv('PHONE_NUMBER')

# logging.basicConfig(level=logging.DEBUG)

# def get_mpesa_access_token():
#     """
#     Fetches the access token for M-Pesa API.
#     """
#     api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
#     consumer_key = CONSUMER_KEY
#     consumer_secret = CONSUMER_SECRET
#     api_key = f"{consumer_key}:{consumer_secret}"
#     headers = {
#         'Authorization': 'Basic ' + base64.b64encode(api_key.encode()).decode()
#     }
#     response = requests.get(api_url, headers=headers)
    
#     logging.debug(f"Status Code: {response.status_code}")
#     logging.debug(f"Response Text: {response.text}")
    
#     if response.status_code == 200:
#         json_response = response.json()
#         return json_response['access_token']
#     else:
#         raise Exception(f"Error getting access token: {response.text}")

# def generate_password(shortcode, passkey):
#     """
#     Generates the password for the M-Pesa payment request.
#     """
#     timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#     data_to_encode = f"{shortcode}{passkey}{timestamp}"
#     encoded_string = base64.b64encode(data_to_encode.encode())
#     return encoded_string.decode('utf-8'), timestamp

# def determine_payment_type(payment_data):
#     """
#     Determines the payment type based on the provided data.
#     """
#     if payment_data.get('order_id'):
#         return 'artwork'
#     elif payment_data.get('booking_id'):
#         return 'event'
#     else:
#         raise ValueError("Cannot determine payment type from provided data")

# def create_payment(payment_data):
#     """
#     Creates a new payment record in the database.
#     """
#     payment_type = determine_payment_type(payment_data)
    
#     payment = Payment(
#         user_id=payment_data.get('user_id'),
#         booking_id=payment_data.get('booking_id'),
#         order_id=payment_data.get('order_id') if payment_type == 'artwork' else None,
#         amount=payment_data['amount'],
#         phone_number=payment_data.get('phone_number'),
#         transaction_id=payment_data.get('transaction_id'),
#         status=payment_data.get('status'),
#         result_desc=payment_data.get('result_desc'),
#         payment_type=payment_type
#     )
#     db.session.add(payment)
#     db.session.commit()

# class TicketResource(Resource):
#     def initiate_payment(self, app, payment_data, payment):
#         """
#         Initiates payment process with M-Pesa.
#         """
#         with app.app_context():
#             access_token = get_mpesa_access_token()
#             headers = {
#                 'Authorization': f'Bearer {access_token}',
#                 'Content-Type': 'application/json'
#             }
#             password, timestamp = generate_password(SHORTCODE, LIPA_NA_MPESA_ONLINE_PASSKEY)
#             payload = {
#                 "BusinessShortCode": SHORTCODE,
#                 "Password": password,
#                 "Timestamp": timestamp,
#                 "TransactionType": "CustomerPayBillOnline",
#                 "Amount": payment_data['amount'],
#                 "PartyA": payment_data['phone_number'],
#                 "PartyB": SHORTCODE,
#                 "PhoneNumber": payment_data['phone_number'],
#                 "CallBackURL": "https://f318-102-214-74-3.ngrok-free.app/callback",  # Replace with your callback URL
#                 "AccountReference": f"Booking ('booking.id')",
#                 "TransactionDesc": "Payment for event ticket purchase. Thank you for your order!"
#             }
# class EventCheckoutResource(Resource):
#     def initiate_mpesa_payment(self, payment_data):
#         user_id = payment_data.get('user_id')
#         booking_id = payment_data.get('booking_id')
#         phone_number = payment_data.get('phone_number')
#         amount = payment_data.get('amount')

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         booking = Booking.query.get(booking_id)
#         if not booking:
#             return {'error': 'Booking not found'}, 404

#         payment = Payment(user_id=user.id, amount=amount, phone_number=phone_number)
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
#             "CallBackURL": "https://b0ca-102-214-74-3.ngrok-free.app/callback", 
#             "AccountReference": f"Booking{booking.id}",
#             "TransactionDesc": "Payment for booking"
#         }

#         try:
#             response = requests.post(
#                 "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
#                 headers=headers,
#                 json=payload
#             )

#             logging.debug(f'M-Pesa API Response: {response.text}')
#             response_data = response.json()
#         except requests.exceptions.RequestException as e:
#             logging.error(f'Error calling M-Pesa API: {e}')
#             payment.status = 'failed'
#             payment.result_desc = 'Failed to connect to M-Pesa API'
#             db.session.commit()
#             return {'error': 'Failed to connect to M-Pesa API'}, 500
#         except ValueError:
#             logging.error(f'Invalid JSON response: {response.text}')
#             payment.status = 'failed'
#             payment.result_desc = 'Invalid response from M-Pesa API'
#             db.session.commit()
#             return {'error': 'Invalid response from M-Pesa API'}, 500

#         if response_data.get('ResponseCode') == '0':
#             payment.transaction_id = response_data['CheckoutRequestID']
#             payment.status = 'initiated'
#             db.session.commit()

#             while True:
#                 payment = Payment.query.filter_by(transaction_id=payment.transaction_id).first()
#                 if payment is None:
#                     logging.error(f'Payment record not found for transaction_id: {payment.transaction_id}')
#                     break
#                 if payment.status == 'completed':
#                     return {'message': 'Payment completed successfully'}, 201
#                 if payment.status == 'failed':
#                     break
#                 time.sleep(1)

#             return {'error': 'Payment failed'}, 400
#         else:
#             payment.status = 'failed'
#             payment.result_desc = response_data.get('ResponseDescription', 'Failed to initiate payment')
#             db.session.commit()
#             return {'error': 'Failed to initiate payment'}, 400

#     def post(self):
#         """
#         Handles ticket purchase and payment initiation via M-Pesa.
#         """
#         args = ticket_parser.parse_args()
#         user_id = args['user_id']
#         ticket_type = args['ticket_type']
#         quantity = args['quantity']
#         phone_number = args['phone_number']

       
#         if not all([user_id, ticket_type, quantity, phone_number]):
#             return {'error': 'All fields are required'}, 400

        
#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

       
#         if not phone_number.startswith("2547") or len(phone_number) != 12:
#             return {"error": "Invalid phone number"}, 400

       
#         ticket = Ticket.query.filter_by(type_name=ticket_type).first()
#         if not ticket:
#             return {'error': 'Invalid ticket type'}, 400

       
#         if ticket.quantity < quantity:
#             return {'error': 'Not enough tickets available'}, 400

        
#         amount = ticket.price * quantity

        
#         ticket.quantity -= quantity
#         db.session.commit()

#         try:
            
#             booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
#             db.session.add(booking)
#             db.session.commit()

#             payment_data = {
#                 'user_id': user_id,
#                 'booking_id': booking.id,
#                 'phone_number': phone_number,
#                 'amount': amount
#             }

#             payment = Payment(
#                 user_id=user_id,
#                 booking_id=booking.id,
#                 amount=amount,
#                 phone_number=phone_number,
#                 status='initiated',
#                 payment_type='event'  
#             )
#             db.session.add(payment)
#             db.session.commit()

            
#             app = current_app._get_current_object()
#             thread = threading.Thread(target=self.initiate_payment, args=(app, payment_data, payment))
#             thread.start()

#             return {
#                 'message': 'Ticket payment initiated successfully',
#                 'booking_id': booking.id
#             }, 201
#         except SQLAlchemyError as e:
#             db.session.rollback()  
#             logging.error(f'Database error: {e}')
#             return {'error': 'An error occurred while processing the order'}, 500
        
        
# class MpesaCallbackResource(Resource):
    
#     def post(self):
#         """
#         Handles the M-Pesa callback for payment status updates.
#         """
#         data = request.get_json()
#         logging.debug(f'Callback Data: {data}')

#         if not data:
#             logging.error("No data received in callback")
#             return {"ResultCode": 1, "ResultDesc": "No data received"}, 400
        
#         try:
#             stk_callback = data['stkCallback']
#             checkout_request_id = stk_callback['CheckoutRequestID']
#             result_code = stk_callback['ResultCode']
#             result_desc = stk_callback['ResultDesc']
#         except KeyError as e:
#             logging.error(f'Missing key in callback data: {e}')
#             return {"ResultCode": 1, "ResultDesc": "Invalid data format"}, 400

#         logging.debug(f'CheckoutRequestID: {checkout_request_id}')
#         logging.debug(f'ResultCode: {result_code}')
#         logging.debug(f'ResultDesc: {result_desc}')

#         payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()
#         if payment:
#             if result_code == 0:
#                 payment.status = 'completed'
#             else:
#                 payment.status = 'failed'
#             payment.result_desc = result_desc
#             db.session.commit()
#             logging.debug(f'Payment status updated to: {payment.status}')
#             return {"ResultCode": 0, "ResultDesc": "Accepted"}, 200
#         else:
#             logging.error(f'Payment record not found for CheckoutRequestID: {checkout_request_id}')
#             return {"ResultCode": 1, "ResultDesc": "Payment record not found"}, 404


# ticket_parser = reqparse.RequestParser()
# ticket_parser.add_argument('user_id', type=int, required=True, help='User ID is required')
# ticket_parser.add_argument('ticket_type', type=str, required=True, help='Ticket type is required')
# ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')
# ticket_parser.add_argument('phone_number', type=str, required=True, help='Phone number is required')


# class TicketResource(Resource):
#     @jwt_required()
#     def get(self):
#         """
#         Retrieves all available ticket types.
#         """
#         tickets = Ticket.query.all()
#         return jsonify([ticket.to_dict() for ticket in tickets])
#     @jwt_required()
#     def post(self):
#         """
#         Handles ticket purchase and payment initiation via M-Pesa.
#         """
#         args = ticket_parser.parse_args()
#         ticket_type = args['ticket_type']
#         quantity = args['quantity']
#         phone_number = args['phone_number']

#         if not phone_number.startswith("2547") or len(phone_number) != 12:
#             return {"error": "Invalid phone number"}, 400


#         ticket = Ticket.query.filter_by(type_name=ticket_type).first()

#         if not ticket:
#             return make_response(jsonify({'message': 'Invalid ticket type'}), 400)


#         if ticket.quantity < quantity:
#             return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

       
#         amount = ticket.price * quantity


#         user_id = 1 
#         booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
#         db.session.add(booking)
#         db.session.commit()

#         payment_data = {
#             'user_id': user_id,
#             'booking_id': booking.id,
#             'phone_number': phone_number,
#             'amount': amount
#         }

#         checkout_resource = EventCheckoutResource()
#         payment_response = checkout_resource.initiate_mpesa_payment(payment_data)

#         if payment_response[1] != 201:
#             return {'error': 'Failed to initiate payment'}, 400

#         return {
#             'message': 'Ticket purchased and payment initiated successfully',
#             'booking_id': booking.id,
#             'payment_response': payment_response
#         }, 201


# import base64
# import json
# import logging
# import os
# import threading
# import time
# from datetime import datetime
# from flask_jwt_extended import jwt_required
# import requests
# from dotenv import load_dotenv
# from flask import request, current_app, make_response, jsonify
# from flask_restful import Resource, reqparse
# from sqlalchemy.exc import SQLAlchemyError
# from models import db, Ticket, Booking, User, Payment

# load_dotenv()

# CONSUMER_KEY = os.getenv('CONSUMER_KEY')
# CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
# SHORTCODE = os.getenv('SHORTCODE')
# LIPA_NA_MPESA_ONLINE_PASSKEY = os.getenv('LIPA_NA_MPESA_ONLINE_PASSKEY')

# logging.basicConfig(level=logging.DEBUG)

# def get_mpesa_access_token():
#     api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
#     consumer_key = CONSUMER_KEY
#     consumer_secret = CONSUMER_SECRET
#     api_key = f"{consumer_key}:{consumer_secret}"
#     headers = {
#         'Authorization': 'Basic ' + base64.b64encode(api_key.encode()).decode()
#     }
#     response = requests.get(api_url, headers=headers)
#     if response.status_code == 200:
#         json_response = response.json()
#         return json_response['access_token']
#     else:
#         raise Exception(f"Error getting access token: {response.text}")

# def generate_password(shortcode, passkey):
#     timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#     data_to_encode = f"{shortcode}{passkey}{timestamp}"
#     encoded_string = base64.b64encode(data_to_encode.encode())
#     return encoded_string.decode('utf-8'), timestamp

# ticket_parser = reqparse.RequestParser()
# ticket_parser.add_argument('user_id', type=int, required=True, help='User ID is required')
# ticket_parser.add_argument('ticket_type', type=str, required=True, help='Ticket type is required')
# ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')
# ticket_parser.add_argument('phone_number', type=str, required=True, help='Phone number is required')

# # class TicketResource(Resource):
# #     @jwt_required()
# #     def get(self):
# #         tickets = Ticket.query.all()
# #         return jsonify([ticket.to_dict() for ticket in tickets])

# #     @jwt_required()
# #     def post(self):
# #         args = ticket_parser.parse_args()
# #         user_id = args['user_id']
# #         ticket_type = args['ticket_type']
# #         quantity = args['quantity']
# #         phone_number = args['phone_number']

# #         if not phone_number.startswith("2547") or len(phone_number) != 12:
# #             return {"error": "Invalid phone number"}, 400

# #         ticket = Ticket.query.filter_by(type_name=ticket_type).first()

# #         if not ticket:
# #             return make_response(jsonify({'message': 'Invalid ticket type'}), 400)

# #         if ticket.quantity < quantity:
# #             return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

# #         amount = ticket.price * quantity

# #         booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
# #         db.session.add(booking)
# #         db.session.commit()

# #         payment_data = {
# #             'user_id': user_id,
# #             'booking_id': booking.id,
# #             'phone_number': phone_number,
# #             'amount': amount
# #         }

# #         checkout_resource = EventCheckoutResource()
# #         payment_response = checkout_resource.initiate_mpesa_payment(payment_data)
# #         return payment_response

# class TicketResource(Resource):
#     @jwt_required()
#     def post(self):
#         args = ticket_parser.parse_args()
#         user_id = args['user_id']
#         ticket_type = args['ticket_type']
#         quantity = args['quantity']
#         phone_number = args['phone_number']

#         if not phone_number.startswith("2547") or len(phone_number) != 12:
#             return {"error": "Invalid phone number"}, 400

#         ticket = Ticket.query.filter_by(type_name=ticket_type).first()

#         if not ticket:
#             return make_response(jsonify({'message': 'Invalid ticket type'}), 400)

#         if ticket.quantity < quantity:
#             return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

#         amount = ticket.price * quantity

#         booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
#         db.session.add(booking)
#         db.session.commit()

#         payment_data = {
#             'user_id': user_id,
#             'booking_id': booking.id,
#             'phone_number': phone_number,
#             'amount': amount
#         }

#         # Ensure that user_id is available and passed to the EventCheckoutResource
#         checkout_resource = EventCheckoutResource()
#         payment_response = checkout_resource.initiate_mpesa_payment(payment_data)
#         return payment_response


# class EventCheckoutResource(Resource):
#     def initiate_mpesa_payment(self, payment_data):
#         user_id = payment_data.get('user_id')
#         booking_id = payment_data.get('booking_id')
#         phone_number = payment_data.get('phone_number')
#         amount = payment_data.get('amount')

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         booking = Booking.query.get(booking_id)
#         if not booking:
#             return {'error': 'Booking not found'}, 404

#         payment = Payment(user_id=user.id, amount=amount, phone_number=phone_number)
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
#             "CallBackURL": "https://fcbf-102-214-74-3.ngrok-free.app",
#             "AccountReference": f"Booking{booking.id}",
#             "TransactionDesc": "Payment for booking"
#         }

#         try:
#             response = requests.post(
#                 "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
#                 headers=headers,
#                 json=payload
#             )

#             logging.debug(f'M-Pesa API Response: {response.text}')
#             response_data = response.json()
#         except requests.exceptions.RequestException as e:
#             logging.error(f'Error calling M-Pesa API: {e}')
#             payment.status = 'failed'
#             payment.result_desc = 'Failed to connect to M-Pesa API'
#             db.session.commit()
#             return {'error': 'Failed to connect to M-Pesa API'}, 500
#         except ValueError:
#             logging.error(f'Invalid JSON response: {response.text}')
#             payment.status = 'failed'
#             payment.result_desc = 'Invalid response from M-Pesa API'
#             db.session.commit()
#             return {'error': 'Invalid response from M-Pesa API'}, 500

#         if response_data.get('ResponseCode') == '0':
#             payment.transaction_id = response_data['CheckoutRequestID']
#             payment.status = 'initiated'
#             db.session.commit()

#             while True:
#                 payment = Payment.query.filter_by(transaction_id=payment.transaction_id).first()
#                 if payment is None:
#                     logging.error(f'Payment record not found for transaction_id: {payment.transaction_id}')
#                     break
#                 if payment.status == 'completed':
#                     return {'message': 'Payment completed successfully'}, 201
#                 if payment.status == 'failed':
#                     break
#                 time.sleep(1)

#             return {'error': 'Payment failed'}, 400
#         else:
#             payment.status = 'failed'
#             payment.result_desc = response_data.get('ResponseDescription', 'Failed to initiate payment')
#             db.session.commit()
#             return {'error': 'Failed to initiate payment'}, 400

#     def post(self):
#         """
#         Handles ticket purchase and payment initiation via M-Pesa.
#         """
#         args = ticket_parser.parse_args()
#         user_id = args['user_id']
#         ticket_type = args['ticket_type']
#         quantity = args['quantity']
#         phone_number = args['phone_number']

#         if not all([user_id, ticket_type, quantity, phone_number]):
#             return {'error': 'All fields are required'}, 400

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         if not phone_number.startswith("2547") or len(phone_number) != 12:
#             return {"error": "Invalid phone number"}, 400

#         ticket = Ticket.query.filter_by(type_name=ticket_type).first()
#         if not ticket:
#             return {'error': 'Invalid ticket type'}, 400

#         if ticket.quantity < quantity:
#             return {'error': 'Not enough tickets available'}, 400

#         amount = ticket.price * quantity

#         ticket.quantity -= quantity
#         db.session.commit()

#         try:
#             booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
#             db.session.add(booking)
#             db.session.commit()

#             payment_data = {
#                 'user_id': user_id,
#                 'booking_id': booking.id,
#                 'phone_number': phone_number,
#                 'amount': amount
#             }

#             payment = Payment(
#                 user_id=user_id,
#                 booking_id=booking.id,
#                 amount=amount,
#                 phone_number=phone_number,
#                 status='initiated',
#                 payment_type='event'
#             )
#             db.session.add(payment)
#             db.session.commit()

#             app = current_app._get_current_object()
#             thread = threading.Thread(target=self.initiate_mpesa_payment, args=(payment_data,))
#             thread.start()

#             return {
#                 'message': 'Ticket payment initiated successfully',
#                 'booking_id': booking.id
#             }, 201
#         except SQLAlchemyError as e:
#             db.session.rollback()
#             logging.error(f'Database error: {e}')
#             return {'error': 'An error occurred while processing the order'}, 500




# class MpesaCallbackResource(Resource):
#     def post(self):
#         data = request.get_json()

#         if not data:
#             return {"ResultCode": 1, "ResultDesc": "No data received"}, 400
        
#         try:
#             stk_callback = data['stkCallback']
#             checkout_request_id = stk_callback['CheckoutRequestID']
#             result_code = stk_callback['ResultCode']
#             result_desc = stk_callback['ResultDesc']
#         except KeyError as e:
#             return {"ResultCode": 1, "ResultDesc": "Invalid data format"}, 400

#         payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()
#         if payment:
#             if result_code == 0:
#                 payment.status = 'completed'
#             else:
#                 payment.status = 'failed'
#             payment.result_desc = result_desc
#             db.session.commit()
#             return {"ResultCode": 0, "ResultDesc": "Confirmation received successfully"}
#         else:
#             return {"ResultCode": 1, "ResultDesc": "Payment not found"}, 


import base64
import json
import logging
import os
import threading
import time
from datetime import datetime
from flask_jwt_extended import jwt_required
import requests
from dotenv import load_dotenv
from flask import request, current_app, make_response, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy.exc import SQLAlchemyError
from models import db, Ticket, Booking, User, Payment

load_dotenv()

CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
SHORTCODE = os.getenv('SHORTCODE')
LIPA_NA_MPESA_ONLINE_PASSKEY = os.getenv('LIPA_NA_MPESA_ONLINE_PASSKEY')

logging.basicConfig(level=logging.DEBUG)

def get_mpesa_access_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = CONSUMER_KEY
    consumer_secret = CONSUMER_SECRET
    api_key = f"{consumer_key}:{consumer_secret}"
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(api_key.encode()).decode()
    }
    response = requests.get(api_url, headers=headers)
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

ticket_parser = reqparse.RequestParser()
ticket_parser.add_argument('user_id', type=int, required=True, help='User ID is required')
ticket_parser.add_argument('ticket_type', type=str, required=True, help='Ticket type is required')
ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')
ticket_parser.add_argument('phone_number', type=str, required=True, help='Phone number is required')

class TicketResource(Resource):
    @jwt_required()
    def post(self):
        args = ticket_parser.parse_args()
        logging.debug(f'Received args: {args}')
        user_id = args['user_id']
        ticket_type = args['ticket_type']
        quantity = args['quantity']
        phone_number = args['phone_number']

        if not phone_number.startswith("2547") or len(phone_number) != 12:
            return {"error": "Invalid phone number"}, 400

        ticket = Ticket.query.filter_by(type_name=ticket_type).first()
        if not ticket:
            return make_response(jsonify({'message': 'Invalid ticket type'}), 400)

        if ticket.quantity < quantity:
            return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

        amount = ticket.price * quantity

        booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
        db.session.add(booking)
        db.session.commit()

        payment_data = {
            'user_id': user_id,
            'booking_id': booking.id,
            'phone_number': phone_number,
            'amount': amount
        }

        # Ensure that user_id is available and passed to the EventCheckoutResource
        checkout_resource = EventCheckoutResource()
        payment_response = checkout_resource.initiate_mpesa_payment(payment_data)
        return payment_response


class EventCheckoutResource(Resource):
    def initiate_mpesa_payment(self, payment_data):
        user_id = payment_data.get('user_id')
        booking_id = payment_data.get('booking_id')
        phone_number = payment_data.get('phone_number')
        amount = payment_data.get('amount')

        try:
            # Retrieve access token
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
                "CallBackURL": "https://e9b4-102-214-72-2.ngrok-free.app/callback",
                "AccountReference": f"Booking{booking_id}",
                "TransactionDesc": "Payment for booking"
            }

            # Send payment request
            response = requests.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                headers=headers,
                json=payload
            )
            response.raise_for_status()  # Raise HTTPError for bad responses

            response_data = response.json()
            logging.debug(f'M-Pesa API Response: {response_data}')

            # Check M-Pesa response
            if response_data.get('ResponseCode') == '0':
                # Payment initiated successfully
                payment = Payment.query.filter_by(booking_id=booking_id).first()
                if payment:
                    payment.transaction_id = response_data['CheckoutRequestID']
                    payment.status = 'initiated'
                    db.session.commit()
                    return {'message': 'Payment initiated successfully'}, 201
                else:
                    logging.error(f'Payment record not found for booking_id: {booking_id}')
                    return {'error': 'Payment record not found'}, 404
            else:
                # Handle error response from M-Pesa
                payment = Payment.query.filter_by(booking_id=booking_id).first()
                if payment:
                    payment.status = 'failed'
                    payment.result_desc = response_data.get('ResponseDescription', 'Failed to initiate payment')
                    db.session.commit()
                return {'error': 'Failed to initiate payment'}, 400

        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling M-Pesa API: {e}')
            payment = Payment.query.filter_by(booking_id=booking_id).first()
            if payment:
                payment.status = 'failed'
                payment.result_desc = 'Failed to connect to M-Pesa API'
                db.session.commit()
            return {'error': 'Failed to connect to M-Pesa API'}, 500
        except ValueError:
            logging.error('Invalid JSON response from M-Pesa API')
            payment = Payment.query.filter_by(booking_id=booking_id).first()
            if payment:
                payment.status = 'failed'
                payment.result_desc = 'Invalid response from M-Pesa API'
                db.session.commit()
            return {'error': 'Invalid response from M-Pesa API'}, 500

    def post(self):
        """
        Handles ticket purchase and payment initiation via M-Pesa.
        """
        args = ticket_parser.parse_args()
        user_id = args['user_id']
        ticket_type = args['ticket_type']
        quantity = args['quantity']
        phone_number = args['phone_number']

        if not all([user_id, ticket_type, quantity, phone_number]):
            return {'error': 'All fields are required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        if not phone_number.startswith("2547") or len(phone_number) != 12:
            return {"error": "Invalid phone number"}, 400

        ticket = Ticket.query.filter_by(type_name=ticket_type).first()
        if not ticket:
            return {'error': 'Invalid ticket type'}, 400

        if ticket.quantity < quantity:
            return {'error': 'Not enough tickets available'}, 400

        amount = ticket.price * quantity

        ticket.quantity -= quantity
        db.session.commit()

        try:
            booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
            db.session.add(booking)
            db.session.commit()

            payment_data = {
                'user_id': user_id,
                'booking_id': booking.id,
                'phone_number': phone_number,
                'amount': amount
            }

            payment = Payment(
                user_id=user_id,
                booking_id=booking.id,
                amount=amount,
                phone_number=phone_number,
                status='initiated',
                payment_type='event'
            )
            db.session.add(payment)
            db.session.commit()

            app = current_app._get_current_object()
            thread = threading.Thread(target=self.initiate_mpesa_payment, args=(payment_data,))
            thread.start()

            return {
                'message': 'Ticket payment initiated successfully',
                'booking_id': booking.id
            }, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Database error: {e}')
            return {'error': 'An error occurred while processing the order'}, 500

class MpesaCallbackResource(Resource):
    def post(self):
        callback_data = request.get_json()

        logging.debug(f'M-Pesa Callback Data: {callback_data}')

        if not callback_data:
            return {'error': 'No data received from M-Pesa'}, 400

        payment_response_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        payment_response_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

        if payment_response_code == '0':
            transaction_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            if payment:
                payment.status = 'completed'
                payment.result_desc = payment_response_desc
                db.session.commit()
                return {'message': 'Payment completed successfully'}, 200
            else:
                logging.error(f'Payment record not found for transaction_id: {transaction_id}')
                return {'error': 'Payment record not found'}, 404
        else:
            transaction_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            if payment:
                payment.status = 'failed'
                payment.result_desc = payment_response_desc
                db.session.commit()
            return {'error': 'Payment failed'}, 400




