from flask_restful import Resource, reqparse
from flask import jsonify, make_response
from models import db, Ticket, Booking

# Define the request parser for ticket buying operations
ticket_parser = reqparse.RequestParser()
ticket_parser.add_argument('ticket_type', type=str, required=True, help='Ticket type is required')
ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')

class TicketResource(Resource):
    def get(self):
        # Retrieve all available ticket types
        tickets = Ticket.query.all()
        return jsonify([ticket.to_dict() for ticket in tickets])

    def post(self):
        args = ticket_parser.parse_args()

        ticket_type = args['ticket_type']
        quantity = args['quantity']

        # Find the ticket type in the database
        ticket = Ticket.query.filter_by(type_name=ticket_type).first()

        if not ticket:
            return make_response(jsonify({'message': 'Invalid ticket type'}), 400)

        # Check if there are enough tickets available
        if ticket.quantity < quantity:
            return make_response(jsonify({'message': 'Not enough tickets available'}), 400)

        # Create a booking record
        user_id = 1  # Replace with actual user ID (e.g., from session or login) after authentication
        booking = Booking(user_id=user_id, event_id=ticket.event_id, ticket_id=ticket.id, status='Confirmed')

        # Update ticket quantity
        ticket.quantity -= quantity

        # Save changes to the database
        db.session.add(booking)
        db.session.commit()

        return make_response(jsonify({'message': 'Tickets booked successfully!'}), 201)
