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
    def initiate_mpesa_payment(self, app, payment_data):
        with app.app_context():
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
                    "CallBackURL": " https://8b73-102-214-72-2.ngrok-free.app/callback",
                    "AccountReference": f"Booking{booking_id}",
                    "TransactionDesc": "Payment for booking"
                }

                # Log the payload for debugging
                logging.debug(f'Sending M-Pesa API request with payload: {payload}')

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
                    logging.error(f'Failed M-Pesa transaction: {response_data}')
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
            except ValueError as e:
                logging.error(f'Invalid JSON response from M-Pesa API: {e}')
                payment = Payment.query.filter_by(booking_id=booking_id).first()
                if payment:
                    payment.status = 'failed'
                    payment.result_desc = 'Invalid response from M-Pesa API'
                    db.session.commit()
                return {'error': 'Invalid response from M-Pesa API'}, 500

    def post(self):
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

            # Pass the current app context to the thread
            app = current_app._get_current_object()
            thread = threading.Thread(target=self.initiate_mpesa_payment, args=(app, payment_data,))
            thread.start()

            return {
                'message': 'Ticket payment initiated successfully',
                'booking_id': booking.id
            }, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Database error: {e}')
            return {'error': 'An error occurred while processing the order'}, 500


# class EventCheckoutResource(Resource):
#     @staticmethod
#     def initiate_mpesa_payment(payment_data):
#         if not isinstance(payment_data, dict):
#             logging.error(f'Expected a dictionary but got: {type(payment_data)}')
#             return {'error': 'Invalid payment data format'}, 400

#         logging.debug(f'Payment data: {payment_data}')

#         user_id = payment_data.get('user_id')
#         booking_id = payment_data.get('booking_id')
#         phone_number = payment_data.get('phone_number')
#         amount = payment_data.get('amount')

#         if not all([user_id, booking_id, phone_number, amount]):
#             logging.error('Missing required fields in payment data')
#             return {'error': 'Missing required fields'}, 400

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         booking = Booking.query.get(booking_id)
#         if not booking:
#             return {'error': 'Booking not found'}, 404

#         payment = Payment(
#             user_id=user.id,
#             booking_id=booking.id,
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
#             "CallBackURL": "https://8b73-102-214-72-2.ngrok-free.app/callback",  # Update with your actual callback URL
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
#             logging.debug(f'User ID: {user_id}')

#             data = request.get_json()
#             if not data:
#                 return {'error': 'No input data provided'}, 400
#             logging.debug(f'Request data: {data}')

#             phone_number = data.get('phone_number')
#             if not phone_number:
#                 return {'error': 'Phone number is required'}, 400

#             ticket_type = data.get('ticket_type')
#             quantity = data.get('quantity', 1)

#             if not all([ticket_type, quantity]):
#                 return {'error': 'Ticket type and quantity are required'}, 400

#             user = User.query.get(user_id)
#             if not user:
#                 return {'error': 'User not found'}, 404

#             # Assuming you have a Ticket model that holds the price for each ticket type
#             ticket = Ticket.query.filter_by(type=ticket_type).first()
#             if not ticket:
#                 return {'error': f'Ticket type {ticket_type} not found'}, 404

#             total_amount = ticket.price * quantity

#             logging.debug(f'Total amount calculated: {total_amount}')

#             booking = Booking(user_id=user.id, total_price=total_amount)
#             db.session.add(booking)
#             db.session.flush()  # Ensure the booking.id is available

#             booking_item = BookingItem(
#                 booking_id=booking.id,
#                 ticket_type=ticket_type,
#                 quantity=quantity,
#                 price=ticket.price,
#             )
#             db.session.add(booking_item)

#             db.session.commit()

#             payment_data = {
#                 'user_id': user.id,
#                 'booking_id': booking.id,
#                 'phone_number': phone_number,
#                 'amount': total_amount
#             }

#             logging.debug(f'Payment data: {payment_data}')
#             payment_response, status_code = self.initiate_mpesa_payment(payment_data)

#             if status_code != 201:
#                 db.session.rollback()
#                 return payment_response, 400

#             return {
#                 'message': 'Booking created and payment initiated successfully',
#                 'booking_id': booking.id,
#                 'transaction_desc': payment_response.get('transaction_desc')
#             }, 201

#         except SQLAlchemyError as e:
#             db.session.rollback()
#             logging.error(f'Database error: {e}')
#             return {'error': 'An error occurred while processing the booking'}, 500
#         except Exception as e:
#             logging.error(f'Unexpected error: {e}')
#             return {'error': 'An unexpected error occurred'}, 500


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




