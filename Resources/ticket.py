from flask_restful import Resource, reqparse
from flask import jsonify,make_response
from models import db, Ticket

# Define the request parser for ticket operations
ticket_parser = reqparse.RequestParser()
ticket_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
ticket_parser.add_argument('price', type=int, required=True, help='Price is required')
ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')

class TicketResource(Resource):
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
        args = ticket_parser.parse_args()

        ticket = Ticket(
                event_id=args['event_id'],
                price=args['price'],
                quantity=args['quantity']
            )
        db.session.add(ticket)
        db.session.commit()
        return make_response(jsonify({'message': 'Ticket bought'}), 201)
    
    def delete(self, id):
        ticket = Ticket.query.get(id)
        if ticket is None:
            return {"error": "Ticket not found"}, 404
        
        db.session.delete(ticket)
        db.session.commit()
        return make_response(jsonify({"message": "Ticket deleted"}), 200)
        
        
