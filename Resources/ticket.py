import base64
import json
import logging
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request
from flask_restful import Resource, reqparse

from models import db, Ticket, Booking, Payment

# Initialize Flask application
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# M-Pesa API credentials
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
SHORTCODE = os.getenv('SHORTCODE')
LIPA_NA_MPESA_ONLINE_PASSKEY = os.getenv('LIPA_NA_MPESA_ONLINE_PASSKEY')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def get_mpesa_access_token():
    """
    Fetches the access token for M-Pesa API.
    """
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    api_key = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
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
    """
    Generates the password for the M-Pesa payment request.
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8'), timestamp

# Define the request parser for ticket buying operations
ticket_parser = reqparse.RequestParser()
ticket_parser.add_argument('ticket_type', type=str, required=True, help='Ticket type is required')
ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')
ticket_parser.add_argument('phone_number', type=str, required=True, help='Phone number is required')

class TicketResource(Resource):
    def get(self):
        """
        Retrieves all available ticket types.
        """
        tickets = Ticket.query.all()
        return jsonify([ticket.to_dict() for ticket in tickets])

    def post(self):
        """
        Handles ticket purchase and payment initiation via M-Pesa.
        """
        args = ticket_parser.parse_args()
        ticket_type = args['ticket_type']
        quantity = args['quantity']
        phone_number = request.json.get('phone_number')  # Get phone number from request

        # Validate phone number format
        if not phone_number.startswith("2547") or len(phone_number) != 12:
            return {"error": "Invalid phone number"}, 400

        # Find the ticket type in the database
        ticket = Ticket.query.filter_by(type_name=ticket_type).first()

        if not ticket:
            return make_response(jsonify({'message': 'Invalid ticket type'}), 400)

        # Check if there are enough tickets available
        if ticket.quantity < quantity:
            return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

        # Calculate the total amount to be paid
        amount = ticket.price * quantity

        # Create a new Booking record
        user_id = 1  # Replace with actual user ID (e.g., from session or login) after authentication
        booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='pending')
        db.session.add(booking)
        db.session.commit()

        # Call M-Pesa API to initiate payment
        try:
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
                "PartyA":  phone_number,
                "PartyB": SHORTCODE,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://ab30-102-214-74-3.ngrok-free.app/callback", 
                "AccountReference": f"Ticket{ticket.id}",
                "TransactionDesc": "Payment for ticket"
            }

            response = requests.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                headers=headers,
                json=payload
            )

            logging.debug(f'M-Pesa API Response: {response.text}')
            response_data = response.json()

            if response_data.get('ResponseCode') == '0':
                booking.transaction_id = response_data['CheckoutRequestID']
                booking.status = 'initiated'
                db.session.commit()
                return {'message': 'Payment initiated successfully'}, 201
            else:
                return {'error': 'Failed to initiate payment'}, 400

        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling M-Pesa API: {e}')
            return {'error': 'Failed to connect to M-Pesa API'}, 500
        except ValueError:
            logging.error(f'Invalid JSON response: {response.text}')
            return {'error': 'Invalid response from M-Pesa API'}, 500

class MpesaCallbackResource(Resource):
    def post(self):
        """
        Handles the M-Pesa callback for payment status updates.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('Body', type=dict, required=True, help='Body is required')
        args = parser.parse_args()

        data = args['Body']

        # Log the incoming callback data for debugging
        logging.debug(f'Callback Data: {data}')

        if not data:
            logging.error("No data received in callback")
            return {"ResultCode": 1, "ResultDesc": "No data received"}, 400
        
        # Process the callback data and update payment status
        try:
            stk_callback = data['stkCallback']
            checkout_request_id = stk_callback['CheckoutRequestID']
            result_code = stk_callback['ResultCode']
            result_desc = stk_callback['ResultDesc']
        except KeyError as e:
            logging.error(f'Missing key in callback data: {e}')
            return {"ResultCode": 1, "ResultDesc": "Invalid data format"}, 400

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
            else:
                payment.status = 'failed'
                payment.result_desc = result_desc
            db.session.commit()
            logging.debug(f'Payment status updated to: {payment.status}')
            return {"ResultCode": 0, "ResultDesc": "Accepted"}, 200
        else:
            logging.error(f'Payment record not found for CheckoutRequestID: {checkout_request_id}')
            return {"ResultCode": 1, "ResultDesc": "Payment record not found"}, 404
