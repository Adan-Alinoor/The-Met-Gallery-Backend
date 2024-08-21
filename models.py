from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)
login_manager = LoginManager()

class Artwork(db.Model, SerializerMixin):
    __tablename__ = 'artworks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    serialize_only = ('id', 'title', 'description', 'price', 'image', 'created_at')

class User(db.Model, SerializerMixin, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)  
    is_seller = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean)

    
    

    cart = db.relationship('Cart', back_populates='user', uselist=False)
    payments = db.relationship('Payment', back_populates='user')
    orders = db.relationship('Order', back_populates='user')
    bookings = db.relationship('Booking', back_populates='user')
    shipping_addresses = db.relationship('ShippingAddress', back_populates='user', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender_user', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient_user', cascade='all, delete-orphan')
    activities = db.relationship('UserActivity', back_populates='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')

    serialize_only = ('id', 'username', 'email', 'role', 'is_admin', 'created_at')

class Booking(db.Model, SerializerMixin):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    status = db.Column(db.String, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='bookings')
    event = db.relationship('Event', back_populates='bookings')
    ticket = db.relationship('Ticket', back_populates='bookings')
    payments = db.relationship('Payment', back_populates='booking', cascade='all, delete-orphan')

    serialize_only = ('id', 'user_id', 'event_id', 'ticket_id', 'status', 'created_at')
    serialize_rules = ('-user.bookings', '-event.bookings', '-ticket.bookings', '-payments.booking')


class Event(db.Model, SerializerMixin):
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

class Ticket(db.Model, SerializerMixin):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    type_name = db.Column(db.String, nullable=False) 
    price = db.Column(db.Integer, nullable=False)  
    quantity = db.Column(db.Integer, nullable=False)
    
    event = db.relationship('Event', back_populates='tickets')
    bookings = db.relationship('Booking', back_populates='ticket')

    serialize_only = ('id', 'event_id', 'type_name', 'price', 'quantity')
    serialize_rules = ('-event.tickets', '-bookings.ticket')

class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sess = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')
    
    serialize_only = ('id', 'user_id', 'items')

class CartItem(db.Model, SerializerMixin):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    
    def to_dict(self):
        return{
            'id': self.id,
            'cart_id': self.cart_id,
            'cart': self.cart.to_dict(),
            'artwork_id': self.artwork_id,
            'quantity': self.quantity,
            'artwork': self.artwork.to_dict() if self.artwork else None  # Add artwork data if it exists, else return None
        }

    cart = db.relationship('Cart', back_populates='items')
    artwork = db.relationship('Artwork')

    serialize_only = ('id', 'cart_id', 'artwork_id', 'quantity')
    serialize_rules = ('-cart.items', '-artwork')

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String, default='pending')
    total_price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order')

    serialize_only = ('id', 'user_id', 'status', 'total_price', 'created_at')

class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String, nullable=True)

    order = db.relationship('Order', back_populates='items')
    artwork = db.relationship('Artwork')

    serialize_only = ('id', 'order_id', 'artwork_id', 'quantity', 'price', 'title', 'description', 'image')
    serialize_rules = ('-order.items', '-artwork')

class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))  # Add this line
    amount = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.String(50), nullable=True) 
    status = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    payment_type = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='payments')
    order = db.relationship('Order', back_populates='payments')
    booking = db.relationship('Booking', back_populates='payments')  # Add this line

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'booking_id': self.booking_id,
            'amount': self.amount,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'phone_number': self.phone_number,
            'payment_type': self.payment_type,
            'created_at': self.created_at.isoformat(), 
            'updated_at': self.updated_at.isoformat(), 
        }


class ShippingAddress(db.Model, SerializerMixin):
    __tablename__ = 'shipping_addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)

    user = db.relationship('User', back_populates='shipping_addresses')

    serialize_only = ('id', 'user_id', 'full_name', 'email', 'address', 'city', 'country', 'phone')

class Message(db.Model, SerializerMixin):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender_user = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient_user = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')

    serialize_only = ('id', 'sender_id', 'recipient_id', 'content', 'sent_at')

class UserActivity(db.Model, SerializerMixin):
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    activity_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='activities')

    serialize_only = ('id', 'user_id', 'activity_type', 'description', 'created_at')

class Notification(db.Model, SerializerMixin):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')

    serialize_only = ('id', 'user_id', 'message', 'created_at')