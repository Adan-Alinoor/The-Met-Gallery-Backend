from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    shipping_addresses = db.relationship('ShippingAddress', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    artworks = db.relationship('Artwork', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.name}>'

class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    orders = db.relationship('Order', backref='artwork', lazy=True)

    def __repr__(self):
        return f'<Artwork {self.title}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('shipping_address.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Order {self.id} by {self.user.username}>'

class ShippingAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    orders = db.relationship('Order', backref='shipping_address', lazy=True)

    def __repr__(self):
        return f'<ShippingAddress {self.full_name} in {self.city}>'

# Main entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all the database tables
    app.run(debug=True)
