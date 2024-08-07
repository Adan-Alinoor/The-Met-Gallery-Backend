from flask import request
from flask_restful import Resource
from models import db,Booking

class BookingResource(Resource):
    def post(self):
        data = request.get_json()
        new_booking = Booking(
            user_id=data['user_id'],
            event_id=data['event_id'],
            status='booked'
        )
        db.session.add(new_booking)
        db.session.commit()
        return {'message': 'Booking created successfully', 'booking_id': new_booking.id}, 201