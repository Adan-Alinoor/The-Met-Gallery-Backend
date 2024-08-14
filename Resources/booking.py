from flask_restful import Resource, reqparse
from datetime import datetime
from models import db, Booking, User, Event, Ticket
from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, get_jwt_identity

booking_parser = reqparse.RequestParser()
booking_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
booking_parser.add_argument('ticket_id', type=int, required=True, help='Ticket ID is required')
booking_parser.add_argument('status', type=str, required=True, help='Status is required')

class BookingResource(Resource):
    @jwt_required()
    def get(self, id=None):
        current_user = get_jwt_identity()
        
        if id is None:
            bookings = Booking.query.all()
            return jsonify([booking.to_dict() for booking in bookings])
        else:
           
            booking = Booking.query.get(id)
            if booking is None:
                return {"error": "Booking not found"}, 404
            return jsonify(booking.to_dict())
        
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()  
        args = booking_parser.parse_args()

        if args['status'] not in ['confirmed', 'pending', 'canceled']:
            return {"error": "Invalid status value"}, 400

        new_booking = Booking(
            user_id=current_user,
            event_id=args['event_id'],
            ticket_id=args['ticket_id'],
            status=args['status'],
            created_at=datetime.utcnow()
        )
        db.session.add(new_booking)
        db.session.commit()
        return make_response(jsonify({'message': 'Booking created successfully'}), 201)
    
    @jwt_required()
    def patch(self, id):
        current_user = get_jwt_identity()  
        args = request.get_json()
        current_user = get_jwt_identity()

        booking = Booking.query.get(id)
        if booking is None:
            return {"error": "Booking not found"}, 404

        if 'status' in args:
            status = args['status']
            if status not in ['confirmed', 'pending', 'canceled']:
                return {"error": "Invalid status value"}, 400
            booking.status = status
            db.session.commit()
            return jsonify(booking.to_dict())
        
        return {"error": "Status not provided"}, 400

    @jwt_required()
    def delete(self, id):
        current_user = get_jwt_identity()

        booking = Booking.query.get(id)
        if booking is None:
            return {"error": "Booking not found"}, 404
        
        db.session.delete(booking)
        db.session.commit()
        return make_response(jsonify({'message': 'Booking deleted'}), 200)
