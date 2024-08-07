from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String,nullable=False)
    email = db.Column(db.String)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String)

    bookings = db.relationship('Booking', back_populates='user')
    payments = db.relationship('Payment', back_populates='user')
    

    serialize_only = ('id', 'username', 'email', 'role')

class Events(db.Model, SerializerMixin):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    description = db.Column(db.String, nullable=False)
    start_date = db.Column(db.Date, nullable=False)  
    end_date = db.Column(db.Date, nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String, nullable=False)

    bookings = db.relationship('Booking', back_populates='event')
    tickets = db.relationship('Ticket', back_populates='event') 

    serialize_rules = ('-bookings', '-tickets')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'image_url': self.image_url,
            'description': self.description,
            'start_date': self.start_date.isoformat(), 
            'end_date': self.end_date.isoformat(), 
            'user_id': self.user_id,
            'time': self.time.isoformat(),
            'created_at': self.created_at.isoformat(),
            'location': self.location
        }

    def __repr__(self):
        return f"Event('{self.title}', '{self.start_date}')"

class Booking(db.Model, SerializerMixin):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    status = db.Column(db.String, default='pending')  # e.g., 'Confirmed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='bookings')
    event = db.relationship('Events', back_populates='bookings')
    ticket = db.relationship('Ticket', back_populates='bookings')
    payments = db.relationship('Payment', back_populates='bookings') 

    serialize_only = ('id', 'user_id', 'event_id', 'ticket_id', 'status', 'created_at')
    serialize_rules = ('user', 'event', 'ticket', 'payment')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id':self.user_id,
            'event_id': self.event_id,
            'ticket_id': self.ticket_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"Booking('{self.user_id}', '{self.event_id}', '{self.ticket_id}')"
    


class Ticket(db.Model, SerializerMixin):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    type_name = db.Column(db.String, nullable=False)  # E.g., 'Regular', 'VIP', 'VVIP'
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False) # Total quantity of ticket type
    
    event = db.relationship('Events', back_populates='tickets')
    bookings = db.relationship('Booking', back_populates='ticket')

    serialize_only = ('id', 'event_id', 'type_name', 'price', 'quantity')
    serialize_rules = ('event', 'bookings')

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'type_name': self.type_name,
            'price': self.price,
            'quantity': self.quantity
        }

    def __repr__(self):
        return f"Ticket('{self.event_id}', '{self.type_name}', '{self.price}', '{self.quantity}')"

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    amount = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    transaction_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    result_desc = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', back_populates='payments')
    bookings = db.relationship('Booking', back_populates='payments')


