from flask_restful import Resource, reqparse
from flask import jsonify, make_response
from models import db, Ticket

# Define a parser for creating and updating tickets
ticket_admin_parser = reqparse.RequestParser()
ticket_admin_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
ticket_admin_parser.add_argument('type_name', type=str, required=True, help='Ticket type name is required')
ticket_admin_parser.add_argument('price', type=float, required=True, help='Ticket price is required')
ticket_admin_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')

class TicketAdminResource(Resource):
    def get(self, id=None):
        if id is None:
            # Retrieve all tickets
            tickets = Ticket.query.all()
            return jsonify([ticket.to_dict() for ticket in tickets])
        else:
            # Retrieve a specific ticket by ID
            ticket = Ticket.query.get(id)
            if ticket is None:
                return {"error": "Ticket not found"}, 404
            return jsonify(ticket.to_dict())
        
    def post(self):
        args = ticket_admin_parser.parse_args()

        # Create a new ticket
        ticket = Ticket(
            event_id=args['event_id'],
            type_name=args['type_name'],
            price=args['price'],
            quantity=args['quantity']
        )

        # Add and commit the new ticket to the database
        db.session.add(ticket)
        db.session.commit()

        return make_response(jsonify({'message': 'Ticket added successfully'}), 201)

    def put(self, id):
        args = ticket_admin_parser.parse_args()

        # Find the existing ticket by ID
        ticket = Ticket.query.get(id)
        if ticket is None:
            return {"error": "Ticket not found"}, 404

        # Update ticket details
        ticket.event_id = args['event_id']
        ticket.type_name = args['type_name']
        ticket.price = args['price']
        ticket.quantity = args['quantity']

        # Commit the changes to the database
        db.session.commit()

        return make_response(jsonify({'message': 'Ticket updated successfully'}), 200)

    def delete(self, id):
        ticket = Ticket.query.get(id)
        if ticket is None:
            return {"error": "Ticket not found"}, 404

        # Delete the ticket from the database
        db.session.delete(ticket)
        db.session.commit()

        return make_response(jsonify({'message': 'Ticket deleted successfully'}), 200)
