from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from datetime import datetime
from models import db, Events

# Define a request parser for event data
event_parser = reqparse.RequestParser()
event_parser.add_argument('title', type=str, required=True, help='Title is required')
event_parser.add_argument('image_url', type=str, required=True, help='Image is required')
event_parser.add_argument('description', type=str, required=True, help='Description is required')
event_parser.add_argument('start_date', type=str, required=True, help='Start Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('end_date', type=str, required=True, help='End Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('user_id', type=int, required=True, help='User ID is required')
event_parser.add_argument('time', type=str, required=True, help='Time is required (format: HH:MM)')
event_parser.add_argument('location', type=str, required=True, help='Location is required')

class EventsResource(Resource):

    # Resource for managing events

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

    def delete(self, id):
        # Delete an event by ID
        event = Events.query.get_or_404(id)
        if event is None:
            return {"error": "Event not found"}, 404
        db.session.delete(event)
        db.session.commit()
        return make_response(jsonify({'message': 'Event deleted'}), 200)

    def put(self, id):
        # Update an event by ID
        event = Events.query.get_or_404(id)
        if event is None:
            return {"error": "Event not found"}, 404
    
        args = event_parser.parse_args()

        event.title = args['title']
        event.image_url = args['image_url']
        event.description = args['description']
        event.start_date = datetime.strptime(args['start_date'], '%d-%m-%Y').date()
        event.end_date = datetime.strptime(args['end_date'], '%d-%m-%Y').date()
        event.user_id = args['user_id']
        event.time = datetime.strptime(args['time'], '%H:%M:%S').time()
        event.location = args['location']
    
        db.session.commit()
        return make_response(jsonify({'message': 'Event updated'}), 200)

    def post(self):
        # Create a new event
        args = event_parser.parse_args()

        try:
            event_date = datetime.strptime(args['start_date'], '%d-%m-%Y').date()
            event_time = datetime.strptime(args['time'], '%H:%M:%S').time()
            created_at = datetime.now()

            new_event = Events(
                title=args['title'],
                image_url=args['image_url'],
                description=args['description'],
                start_date=event_date,
                end_date=datetime.strptime(args['end_date'], '%d-%m-%Y').date(),
                user_id=args['user_id'],
                time=event_time,
                created_at=created_at,
                location=args['location']
            )

            db.session.add(new_event)
            db.session.commit()

            return make_response(jsonify({'message': 'Event added'}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f"An error occurred: {str(e)}"}), 500)
