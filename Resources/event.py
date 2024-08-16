from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from models import db, Event, Ticket, User

event_parser = reqparse.RequestParser()
event_parser.add_argument('title', type=str, required=True, help='Title is required')
event_parser.add_argument('image_url', type=str, required=True, help='Image is required')
event_parser.add_argument('description', type=str, required=True, help='Description is required')
event_parser.add_argument('start_date', type=str, required=True, help='Start Date is required (format: YYYY-MM-DD)')
event_parser.add_argument('end_date', type=str, required=True, help='End Date is required (format: YYYY-MM-DD)')
event_parser.add_argument('time', type=str, required=True, help='Time is required (format: HH:MM)')
event_parser.add_argument('location', type=str, required=True, help='Location is required')

class EventsResource(Resource):
    @jwt_required()
    def get(self, id=None):
        try:
            current_user_id = get_jwt_identity()
            user_specific = request.args.get('user_specific', 'false').lower() == 'true'

            if id:
                # Fetch a specific event by ID for the current user
                event = Event.query.filter_by(id=id, user_id=current_user_id).first()
                if event is None:
                    return {"error": "Event not found"}, 404
                event_dict = event.to_dict()
                tickets = Ticket.query.filter_by(event_id=id).all()
                if tickets:
                    event_dict['tickets'] = [ticket.to_dict() for ticket in tickets]
                return event_dict, 200

            if user_specific:
                # Fetch events for the current user
                events = Event.query.filter_by(user_id=current_user_id).all()
            else:
                # Fetch all events
                events = Event.query.all()

            return [event.to_dict() for event in events], 200

        except Exception as e:
            logging.error(f"Error fetching events: {e}")
            return {"error": str(e)}, 500

    @jwt_required()
    def delete(self, id):
        current_user_id = get_jwt_identity()
        try:
            event = Event.query.get_or_404(id)
            user = User.query.get_or_404(current_user_id)

            # Check if the current user is an admin or the owner of the event
            if not user.is_admin and event.user_id != current_user_id:
                return {"error": "Unauthorized access"}, 403

            db.session.delete(event)
            db.session.commit()
            return make_response(jsonify({'message': 'Event deleted'}), 200)
        except Exception as e:
            logging.error(f"Error deleting event: {e}")
            return {"error": f"Error deleting event: {str(e)}"}, 500

    @jwt_required()
    def put(self, id):
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(id)
        if event.user_id != current_user_id:
            return {"error": "Unauthorized access"}, 403

        args = event_parser.parse_args()

        try:
            event.start_date = datetime.strptime(args['start_date'], '%Y-%m-%d').date()
            event.end_date = datetime.strptime(args['end_date'], '%Y-%m-%d').date()
            event.time = datetime.strptime(args['time'], '%H:%M').time()
        except ValueError as e:
            return {"error": str(e)}, 400

        event.title = args['title']
        event.image_url = args['image_url']
        event.description = args['description']
        event.user_id = current_user_id
        event.location = args['location']

        db.session.commit()
        return make_response(jsonify({'message': 'Event updated'}), 200)

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        args = event_parser.parse_args()

        try:
            start_date = datetime.strptime(args['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(args['end_date'], '%Y-%m-%d').date()
            event_time = datetime.strptime(args['time'], '%H:%M').time()
        except ValueError as e:
            return {"error": f"Invalid date format: {str(e)}"}, 400

        try:
            new_event = Event(
                title=args['title'],
                image_url=args['image_url'],
                description=args['description'],
                start_date=start_date,
                end_date=end_date,
                user_id=current_user_id,
                time=event_time,
                created_at=datetime.now(),
                location=args['location']
            )

            db.session.add(new_event)
            db.session.commit()

            # Return the event ID in the response
            return make_response(jsonify({'event_id': new_event.id}), 201)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'error': f"An error occurred: {str(e)}"}), 500)
