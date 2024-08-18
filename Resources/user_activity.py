from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, UserActivity, UserActivitySchema, User

activity_schema = UserActivitySchema()
activities_schema = UserActivitySchema(many=True)

class UserActivityResource(Resource):
    @jwt_required()
    def get(self, user_id=None):
        current_user_id = get_jwt_identity()

        if user_id and user_id != current_user_id:
            return {"message": "Unauthorized access"}, 403

        activities = UserActivity.query.filter_by(user_id=current_user_id).all()
        return activities_schema.dump(activities), 200

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('activity_type', required=True, help='Activity type cannot be blank')
        parser.add_argument('description', required=False)
        parser.add_argument('event_id', required=False, type=int)
        parser.add_argument('artwork_id', required=False, type=int)
        parser.add_argument('payment_id', required=False, type=int)
        args = parser.parse_args()

        current_user_id = get_jwt_identity()

        new_activity = UserActivity(
            user_id=current_user_id,
            activity_type=args['activity_type'],
            description=args.get('description'),
            event_id=args.get('event_id'),
            artwork_id=args.get('artwork_id'),
            payment_id=args.get('payment_id')
        )

        db.session.add(new_activity)
        db.session.commit()

        return activity_schema.dump(new_activity), 201

class UserActivityListResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        activities = UserActivity.query.filter_by(user_id=current_user_id).order_by(UserActivity.created_at.desc()).all()
        return activities_schema.dump(activities), 200
