from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime


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
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'image': self.image,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String)
    
    cart = db.relationship('Cart', back_populates='user', uselist=False)
    payments = db.relationship('Payment', back_populates='user')
    orders = db.relationship('Order', back_populates='user')

    bookings = db.relationship('Booking', back_populates='user')
    payments = db.relationship('Payment', back_populates='user')
    shipping_addresses = db.relationship('ShippingAddress', back_populates='user', cascade='all, delete-orphan')

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
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

class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items]
        }

class CartItem(db.Model, SerializerMixin):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    image = db.Column(db.String(200), nullable=False)

    artwork = db.relationship('Artwork')
    cart = db.relationship('Cart', back_populates='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'artwork_id': self.artwork_id,
            'quantity': self.quantity,
            'price': self.price,
            'title': self.title,
            'description': self.description,
            'image': self.image,
            'artwork': self.artwork.to_dict()
        }

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship("Payment", back_populates="order")
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('shipping_addresses.id'))
    shipping_address = db.relationship('ShippingAddress', back_populates='orders')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Integer, nullable=False)
    
    order = db.relationship('Order', back_populates='items')
    artwork = db.relationship('Artwork')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'artwork_id': self.artwork_id,
            'quantity': self.quantity,
            'price': self.price,
            'artwork': self.artwork.to_dict()
        }

class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    phone_number = db.Column(db.String(20), nullable=False) 
    transaction_code = db.Column(db.String ,nullable=True)
    status = db.Column(db.String(50), default='pending')
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    transaction_desc = db.Column(db.String(255), nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)  

    user = db.relationship('User', back_populates='payments')
    bookings = db.relationship('Booking', back_populates='payments')
    order = db.relationship('Order', back_populates='payments')


class ShippingAddress(db.Model, SerializerMixin):
    __tablename__ = 'shipping_addresses'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='shipping_addresses')
    orders = db.relationship('Order', back_populates='shipping_address')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'phone': self.phone
        }

