
from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Events

# Define a request parser for event data
event_parser = reqparse.RequestParser()
event_parser.add_argument('title', type=str, required=True, help='Title is required')
event_parser.add_argument('image_url', type=str, required=True, help='Image is required')
event_parser.add_argument('description', type=str, required=True, help='Description is required')
event_parser.add_argument('start_date', type=str, required=True, help='Start Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('end_date', type=str, required=True, help='End Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('time', type=str, required=True, help='Time is required (format: HH:MM)')
event_parser.add_argument('location', type=str, required=True, help='Location is required')

class EventsResource(Resource):
    # Resource for managing events

    @jwt_required()  # Requires authentication
    def get(self, id=None):
        # Get all events or a single event by ID
        if id is None:
            # Get all events
            events = Events.query.all()
            return [event.to_dict() for event in events]
        else:
            # Get a single event by id
            event = Events.query.get(id)
            if event is None:
                return {"error": "Event not found"}, 404
            return event.to_dict()

    @jwt_required()  # Requires authentication
    def delete(self, id):
        current_user_id = get_jwt_identity()

        # Delete an event by ID (no need to check for admin for deletion if it's not required)
        event = Events.query.get_or_404(id)
        db.session.delete(event)
        db.session.commit()
        return make_response(jsonify({'message': 'Event deleted'}), 200)

    @jwt_required()  # Requires authentication
    def put(self, id):
        current_user_id = get_jwt_identity()

        # Update an event by ID (no need to check for admin for updating if it's not required)
        event = Events.query.get_or_404(id)
    
        args = event_parser.parse_args()

        # Validate date and time formats
        try:
            event.start_date = datetime.strptime(args['start_date'], '%d-%m-%Y').date()
            event.end_date = datetime.strptime(args['end_date'], '%d-%m-%Y').date()
            event.time = datetime.strptime(args['time'], '%H:%M').time()
        except ValueError as e:
            return {"error": str(e)}, 400

        event.title = args['title']
        event.image_url = args['image_url']
        event.description = args['description']
        event.user_id = current_user_id  # Associate the event with the current user
        event.location = args['location']
    
        db.session.commit()
        return make_response(jsonify({'message': 'Event updated'}), 200)

    @jwt_required()  # Requires authentication
    def post(self):
        current_user_id = get_jwt_identity()  # Get the current user's identity

        args = event_parser.parse_args()

        # Validate date and time formats
        try:
            start_date = datetime.strptime(args['start_date'], '%d-%m-%Y').date()
            end_date = datetime.strptime(args['end_date'], '%d-%m-%Y').date()
            event_time = datetime.strptime(args['time'], '%H:%M').time()
        except ValueError as e:
            return {"error": str(e)}, 400

        try:
            new_event = Events(
                title=args['title'],
                image_url=args['image_url'],
                description=args['description'],
                start_date=start_date,
                end_date=end_date,
                user_id=current_user_id,  # Associate the event with the current user
                time=event_time,
                created_at=datetime.now(),
                location=args['location']
            )

            db.session.add(new_event)
            db.session.commit()

            return make_response(jsonify({'message': 'Event added'}), 201)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f"An error occurred: {str(e)}"}), 500)
