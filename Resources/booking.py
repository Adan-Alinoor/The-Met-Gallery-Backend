from flask_restful import Resource, reqparse
from datetime import datetime
from models import db, Booking, Event
from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

booking_parser = reqparse.RequestParser()

booking_parser.add_argument('event_id', type=int, required=True, help='Event ID is required')
booking_parser.add_argument('ticket_id', type=int, required=True, help='Ticket ID is required')
booking_parser.add_argument('status', type=str, required=True, help='Status is required')

class BookingResource(Resource):
    @jwt_required()
    def get(self, id=None):
        try:
            current_user_id = get_jwt_identity()
            user_specific = request.args.get('user_specific', 'false').lower() == 'true'

            if user_specific:
                # Fetch bookings for the current user
                bookings = Booking.query.filter_by(user_id=current_user_id).all()
            else:
                if id is None:
                    # Fetch all bookings
                    bookings = Booking.query.all()
                else:
                    # Fetch a specific booking by ID
                    booking = Booking.query.get(id)
                    if booking is None:
                        return {"error": "Booking not found"}, 404
                    booking_dict = booking.to_dict()
                    event = Event.query.get(booking.event_id)
                    if event:
                        booking_dict['event'] = event.to_dict()
                    return jsonify(booking_dict), 200

            # Fetch event details for each booking
            bookings_with_event_details = []
            for booking in bookings:
                event = Event.query.get(booking.event_id)
                if event:
                    booking_data = booking.to_dict()
                    event_data = event.to_dict()
                    booking_data.update({"event": event_data})
                    bookings_with_event_details.append(booking_data)

            return jsonify(bookings_with_event_details)

        except Exception as e:
            logging.error(f"Error fetching bookings: {e}")
            return {"error": str(e)}, 500
        

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
