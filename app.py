from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Events, Booking, Ticket
from Resources.event import EventsResource
from Resources.ticket import TicketResource
from Resources.booking import BookingResource
from Resources.admin_ticket import TicketAdminResource
from flask_cors import CORS

app = Flask(__name__)

# db connection
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Add CORS middleware
CORS(app)


migrate = Migrate(app, db)
db.init_app(app)

# Create an instance of the Api class
api = Api(app)

class Home(Resource):
    def get(self):
        response_dict = {"message": "Welcome to The Met Gallery"}
        return jsonify(response_dict)

# Add the EventsResource class as a resource to the API
api.add_resource(Home, '/')
api.add_resource(EventsResource, '/events', '/events/<int:id>')
api.add_resource(TicketResource, '/tickets', '/tickets/<int:id>')
api.add_resource(BookingResource, '/bookings', '/bookings/<int:id>')
api.add_resource(TicketAdminResource, '/admin/tickets', '/admin/tickets/<int:id>')

if __name__ == "__main__":
    app.run(debug=True)