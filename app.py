from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from models import Booking, Notification, Event, UserActivity

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['JWT_SECRET_KEY'] = 'my_jwt_secret_key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

@app.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    current_user_id = get_jwt_identity()

    bookings = Booking.query.filter_by(user_id=current_user_id).all()
    notifications = Notification.query.filter_by(user_id=current_user_id).all()
    user_activities = UserActivity.query.filter_by(user_id=current_user_id).all()
    events = Event.query.all() 

    booking_data = [{
        'id': booking.id,
        'user_id': booking.user_id,
        'artwork_id': booking.artwork_id,
        'booking_date': booking.booking_date.isoformat(),
        'status': booking.status
    } for booking in bookings]

    notification_data = [{
        'id': notification.id,
        'user_id': notification.user_id,
        'message': notification.message,
        'timestamp': notification.timestamp.isoformat()
    } for notification in notifications]

    event_data = [{
        'id': event.id,
        'name': event.name,
        'description': event.description,
        'event_date': event.event_date.isoformat()
    } for event in events]

    user_activity_data = [{
        'id': activity.id,
        'user_id': activity.user_id,
        'activity_type': activity.activity_type,
        'timestamp': activity.timestamp.isoformat()
    } for activity in user_activities]

    response = {
        'bookings': booking_data,
        'notifications': notification_data,
        'events': event_data,
        'user_activities': user_activity_data
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
