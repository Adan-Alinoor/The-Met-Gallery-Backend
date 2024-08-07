import os
from datetime import datetime
from app import app, db
from models import Events, User, Booking, Ticket, Payment, Artworks, Product
from faker import Faker
import logging

# Initialize Faker
fake = Faker()

# Set logging level
logging.basicConfig(level=logging.INFO)

def delete_existing_data():
    with app.app_context():
        logging.info("Deleting existing data...")
        Events.query.delete()
        User.query.delete()
        Booking.query.delete()
        Ticket.query.delete()
        Payment.query.delete()
        Product.query.delete()


def seed_users(num_users=10):
    with app.app_context():
        logging.info("Seeding users...")
        users = [User(username=fake.user_name(), email=fake.email(), password=fake.password(), role='user') for _ in range(num_users)]
        db.session.bulk_save_objects(users)
        db.session.commit()
        logging.info("Users seeded.")

def seed_events():
    events_data = [
        {
            "title": "The Grief Paintings",
            "image_url": "https://images.artnet.com/gallery-images/425937671/95826851-8e2f-4dbe-a10d-e9c97c1b7997.jpg?x=1320%40%211320aD0xMzIwJnc9MTMyMCZmPWNvbnRhaW4mdD1s",
            "description": "An exhibition of new paintings by Helen Marden, created with resin, powdered pigment, ink, and natural objects, reflecting on life, love, and creativity.",
            "start_date": "24-07-2024",
            "end_date": "14-09-2024",
            "user_id": 1,
            "time": "10:00:00",
            "location": "Gagosian 821 Park Avenue New York, NY USA"
        },
        {
            "title": "A Black Revolutionary Artist",
            "image_url": "https://www.nga.gov/content/dam/ngaweb/exhibitions/promos/2025/elizabeth-catlett-black-unity.jpg",
            "description": "Showcasing over 150 works by Elizabeth Catlett, this exhibition explores her career from DC to Mexico, highlighting her focus on social justice.",
            "start_date": "13-09-2024",
            "end_date": "19-01-2025",
            "user_id": 2,
            "time": "20:00:00",
            "location": "Brooklyn Museum of Art"
        },
        {
            "title": "Summer Album",
            "image_url": "https://images.artnet.com/gallery-images/424675664/5e88ef11-6277-4c47-98db-de80afa8d678.jpg?x=1320%40%211320aD0xMzIwJnc9MTMyMCZmPWNvbnRhaW4mdD1s",
            "description": "A curated collection capturing the essence and vibrancy of summer through diverse artworks.",
            "start_date": "26-07-2024",
            "end_date": "07-09-2024",
            "user_id": 3,
            "time": "08:00:00",
            "location": "Ben Brown Fine Arts, Hong Kong China"
        },
        {
            "title": "Sculpting Dreams: Hands-On Sculpture Workshop",
            "image_url": "https://i.pinimg.com/474x/ca/50/26/ca50269e08f91b279490386227b9b6ff.jpg",
            "description": "A dynamic workshop for beginners to explore sculpture using mixed media.",
            "start_date": "12-08-2024",
            "end_date": "15-08-2024",
            "user_id": 4,
            "time": "14:00:00",
            "location": "Art Center Studio, 123 Elm Street, Chicago, IL"
        },
        {
            "title": "Frühe Grafik",
            "image_url": "https://images.artnet.com/gallery-images/115607/1638779.jpg?x=%40%21614xiu8%5EaD0mdz02MTQmZj1jb250YWluJnQ9bA%3D%3D",
            "description": "Bernhard Luginbühl's early graphic works, revealing intricate lines and bold forms.",
            "start_date": "05-09-2024",
            "end_date": "01-11-2024",
            "user_id": 5,
            "time": "12:00:00",
            "location": "Galerie Ziegler, Switzerland"
        },
        {
            "title": "Commemorations",
            "image_url": "https://images.artnet.com/gallery-images/115607/1638779.jpg?x=%40%21614xiu8%5EaD0mdz02MTQmZj1jb250YWluJnQ9bA%3D%3D",
            "description": "Joe Bloom’s solo exhibition featuring stained-glass orbs that symbolize light and tribute.",
            "start_date": "02-08-2024",
            "end_date": "14-09-2024",
            "user_id": 6,
            "time": "10:00:00",
            "location": "Kristin Hjellegjerde Gallery, London"
        }
    ]
    
    with app.app_context():
        logging.info("Seeding events...")
        for event_data in events_data:
            try:
                start_date = datetime.strptime(event_data["start_date"], "%d-%m-%Y").date()
                end_date = datetime.strptime(event_data["end_date"], "%d-%m-%Y").date()
                event_time = datetime.strptime(event_data["time"], "%H:%M:%S").time()

                event = Events(
                    title=event_data["title"],
                    image_url=event_data["image_url"],
                    description=event_data["description"],
                    start_date=start_date,
                    end_date=end_date,
                    user_id=event_data["user_id"],
                    time=event_time,
                    location=event_data["location"],
                    created_at=datetime.utcnow()
                )
                db.session.add(event)
            except Exception as e:
                logging.error(f"Error adding event {event_data['title']}: {e}")

        try:
            db.session.commit()
            logging.info("Events seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing to database: {e}")

def seed_products():
    products_data = [
        {
            "title": "Starry Night",
            "description": "A masterpiece by Vincent van Gogh, depicting a dreamy view from the artist's asylum room.",
            "price": 5000000,
            "image": "https://i.ibb.co/484yd5n/Starry-night.jpg"
        },
        {
            "title": "Mona Lisa",
            "description": "A portrait of Lisa Gherardini, painted by Leonardo da Vinci.",
            "price": 850000000,
            "image": "https://i.ibb.co/yQDhv3z/monalisa.jpg"
        },
        {
            "title": "The Scream",
            "description": "An iconic work by Edvard Munch, symbolizing human anxiety.",
            "price": 120000000,
            "image": "https://i.ibb.co/PMhrqp2/the-scream.jpg"
        },
        {
            "title": "The Persistence of Memory",
            "description": "A surreal painting by Salvador Dalí, showcasing melting clocks.",
            "price": 6000000,
            "image": "https://i.ibb.co/kHxK6FV/The-Persistence-of-Memory.jpg"
        },
        {
            "title": "Girl with a Pearl Earring",
            "description": "An oil painting by Johannes Vermeer, depicting a girl with a pearl earring.",
            "price": 7000000,
            "image": "https://i.ibb.co/dPz3dHT/girlpearlearing.jpg"
        },
        {
            "title": "The Night Watch",
            "description": "A painting by Rembrandt, portraying a group of city guards.",
            "price": 45000000,
            "image": "https://i.ibb.co/GJCgyrG/The-Night-Watch.jpg"
        },
        {
            "title": "Guernica",
            "description": "An anti-war painting by Pablo Picasso, reflecting the bombing of Guernica.",
            "price": 200000000,
            "image": "https://i.ibb.co/gVB8SQK/Picasso-Guernica.jpg"
        },
        {
            "title": "The Birth of Venus",
            "description": "A painting by Sandro Botticelli, depicting Venus emerging from the sea.",
            "price": 100000000,
            "image": "https://i.ibb.co/wwHdp6F/the-venus.jpg"
        },
        {
            "title": "The Kiss",
            "description": "A painting by Gustav Klimt, representing an intimate embrace.",
            "price": 150000000,
            "image": "https://i.ibb.co/PFVyPRw/The-Kiss.jpg"
        },
        {
            "title": "American Gothic",
            "description": "A painting by Grant Wood, showing a farmer and his daughter.",
            "price": 30000000,
            "image": "https://i.ibb.co/5xMc8zq/American-Gothic.jpg"
        },
        {
            "title": "The Arnolfini Portrait",
            "description": "A painting by Jan van Eyck, featuring a double portrait of Giovanni di Nicolao di Arnolfini and his wife.",
            "price": 20000000,
            "image": "https://i.ibb.co/ZjvTs9J/Arnolfini-Portrait.jpg"
        }
    ]
    
    with app.app_context():
        logging.info("Seeding products...")
        for product_data in products_data:
            try:
                product = Product(
                    title=product_data["title"],
                    description=product_data["description"],
                    price=product_data["price"],
                    image=product_data["image"],
                    created_at=datetime.utcnow()
                )
                db.session.add(product)
            except Exception as e:
                logging.error(f"Error adding product {product_data['title']}: {e}")

        try:
            db.session.commit()
            logging.info("Products seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing to database: {e}")

def main():
    logging.info("Starting data seeding...")
    delete_existing_data()
    seed_users()
    seed_events()
    seed_products()
    logging.info("Data seeding completed.")

if __name__ == "__main__":
    main()
