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
    type_name = db.Column(db.String, nullable=False)  # E.g., 'Regular', 'VIP', 'VVIP'
    price = db.Column(db.Integer, nullable=False)  # Keeping price as integer
    quantity = db.Column(db.Integer, nullable=False) # Total quantity of ticket type
    
    event = db.relationship('Event', back_populates='tickets')
    bookings = db.relationship('Booking', back_populates='ticket')

    serialize_only = ('id', 'event_id', 'type_name', 'price', 'quantity')
    serialize_rules = ('-event.tickets', '-bookings.ticket')


class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')
    
    serialize_only = ('id', 'user_id', 'items')


class CartItem(db.Model, SerializerMixin):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False)  # Keeping price as integer
    description = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    cart = db.relationship('Cart', back_populates='items')
    artwork = db.relationship('Artwork')

    serialize_only = ('id', 'cart_id', 'artwork_id', 'quantity', 'price')
    serialize_rules = ('-cart.items', '-artwork')


class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('shipping_addresses.id'), nullable=True)
    
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan')
    shipping_address = db.relationship('ShippingAddress', back_populates='orders')

    serialize_only = ('id', 'user_id', 'created_at', 'items', 'payments', 'shipping_address')


class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False)  # Keeping price as integer
    
    order = db.relationship('Order', back_populates='items')
    artwork = db.relationship('Artwork')

    serialize_only = ('id', 'order_id', 'artwork_id', 'quantity', 'price')
    serialize_rules = ('-order.items', '-artwork')


class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # Keeping amount as integer
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    phone_number = db.Column(db.String(20), nullable=False) 
    transaction_code = db.Column(db.String, nullable=True)
    status = db.Column(db.String(50), default='pending')
    transaction_desc = db.Column(db.String(255), nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)  

    user = db.relationship('User', back_populates='payments')
    booking = db.relationship('Booking', back_populates='payments')
    order = db.relationship('Order', back_populates='payments')

    serialize_only = ('id', 'booking_id', 'order_id', 'amount', 'payment_date', 'status', 'transaction_code')


class ShippingAddress(db.Model, SerializerMixin):
    __tablename__ = 'shipping_addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)

    user = db.relationship('User', back_populates='shipping_addresses')
    orders = db.relationship('Order', back_populates='shipping_address')

    serialize_only = ('id', 'user_id', 'full_name', 'email', 'address', 'city', 'country', 'phone')


class Message(db.Model, SerializerMixin):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender_user = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient_user = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')

    serialize_only = ('id', 'sender_id', 'recipient_id', 'content', 'timestamp', 'is_read')
    serialize_rules = ('-sender_user.sent_messages', '-recipient_user.received_messages')


class UserActivity(db.Model, SerializerMixin):
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='activities')

    serialize_only = ('id', 'user_id', 'action', 'timestamp')


class Notification(db.Model, SerializerMixin):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='notifications')

    serialize_only = ('id', 'user_id', 'content', 'timestamp', 'is_read')
