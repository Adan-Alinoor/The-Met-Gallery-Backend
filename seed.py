from faker import Faker
from models import db, User, Product
import random
from app import app

fake = Faker()

def seed_users(num_users=10):
    User.query.delete()
    for _ in range(num_users):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password()
        )
        db.session.add(user)
    db.session.commit()

def seed_products(num_products=20):
    Product.query.delete()
    for _ in range(num_products):
        product = Product(
            name=fake.word(),
            description=fake.sentence(),
            price = int(random.uniform(10.0, 100.0)) ,
            image=fake.image_url()
        )
        db.session.add(product)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_users()
        seed_products()