from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Events


event_parser = reqparse.RequestParser()
event_parser.add_argument('title', type=str, required=True, help='Title is required')
event_parser.add_argument('image_url', type=str, required=True, help='Image is required')
event_parser.add_argument('description', type=str, required=True, help='Description is required')
event_parser.add_argument('start_date', type=str, required=True, help='Start Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('end_date', type=str, required=True, help='End Date is required (format: DD-MM-YYYY)')
event_parser.add_argument('time', type=str, required=True, help='Time is required (format: HH:MM)')
event_parser.add_argument('location', type=str, required=True, help='Location is required')

class EventsResource(Resource):
  

    @jwt_required() 
    def get(self, id=None):
       
        if id is None:
            
            events = Events.query.all()
            return [event.to_dict() for event in events]
        else:
            
            event = Events.query.get(id)
            if event is None:
                return {"error": "Event not found"}, 404
            return event.to_dict()

    @jwt_required()  
    def delete(self, id):
        current_user_id = get_jwt_identity()

       
        event = Events.query.get_or_404(id)
        db.session.delete(event)
        db.session.commit()
        return make_response(jsonify({'message': 'Event deleted'}), 200)

    @jwt_required()  
    def put(self, id):
        current_user_id = get_jwt_identity()

        event = Events.query.get_or_404(id)
    
        args = event_parser.parse_args()

        try:
            event.start_date = datetime.strptime(args['start_date'], '%d-%m-%Y').date()
            event.end_date = datetime.strptime(args['end_date'], '%d-%m-%Y').date()
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
                user_id=current_user_id,  
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
