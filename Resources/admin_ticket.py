from flask_restful import Resource, reqparse
from flask import jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Ticket
from flask import request



ticket_admin_parser = reqparse.RequestParser()
ticket_admin_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
ticket_admin_parser.add_argument('type_name', type=str, required=True, help='Ticket type name is required')
ticket_admin_parser.add_argument('price', type=float, required=True, help='Ticket price is required')
ticket_admin_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')


ticket_parser = reqparse.RequestParser()
ticket_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
ticket_parser.add_argument('type_name', type=str, required=True, help='Ticket type name is required')
ticket_parser.add_argument('price', type=float, required=True, help='Ticket price is required')
ticket_parser.add_argument('quantity', type=int, required=True, help='Quantity is required')

class TicketAdminResource(Resource):
    @jwt_required()
    def get(self, id=None):
        if id is None:
            # Fetch tickets based on event_id query parameter if provided
            event_id = request.args.get('event_id', type=int)
            if event_id:
                tickets = Ticket.query.filter_by(event_id=event_id).all()
            else:
                tickets = Ticket.query.all()
            return jsonify([ticket.to_dict() for ticket in tickets])
        else:
            ticket = Ticket.query.get(id)
            if ticket is None:
                return {"error": "Ticket not found"}, 404
            return jsonify(ticket.to_dict())

    @jwt_required()
    def post(self):
        args = ticket_parser.parse_args()
        ticket = Ticket(
            event_id=args['event_id'],
            type_name=args['type_name'],
            price=args['price'],
            quantity=args['quantity']
        )
        db.session.add(ticket)
        db.session.commit()
        return make_response(jsonify({'message': 'Ticket added successfully'}), 201)

    @jwt_required()
    def put(self, id):
        args = ticket_parser.parse_args()
        ticket = Ticket.query.get(id)
        if ticket is None:
            return {"error": "Ticket not found"}, 404
        ticket.event_id = args['event_id']
        ticket.type_name = args['type_name']
        ticket.price = args['price']
        ticket.quantity = args['quantity']
        db.session.commit()
        return make_response(jsonify({'message': 'Ticket updated successfully'}), 200)

    @jwt_required()
    def delete(self, id):
        ticket = Ticket.query.get(id)
        if ticket is None:
            return {"error": "Ticket not found"}, 404
        db.session.delete(ticket)
        db.session.commit()
        return make_response(jsonify({'message': 'Ticket deleted successfully'}), 200)