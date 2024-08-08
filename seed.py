
import os
from datetime import datetime
from app import app, db
from models import Events, User, Booking, Ticket, Payment, Artwork,OrderItem,Order,Cart,CartItem,ShippingAddress
from faker import Faker
import logging

# Initialize Faker
fake = Faker()

# Set logging level
logging.basicConfig(level=logging.INFO)

def delete_existing_data():
    with app.app_context():
        logging.info("Starting data deletion process...")
        try:
            # Delete data from dependent tables first
            logging.info("Deleting data from OrderItems...")
            OrderItem.query.delete()

            logging.info("Deleting data from Orders...")
            Order.query.delete()

            logging.info("Deleting data from Payments...")
            Payment.query.delete()

            logging.info("Deleting data from Bookings...")
            Booking.query.delete()

            logging.info("Deleting data from Tickets...")
            Ticket.query.delete()

            logging.info("Deleting data from Events...")
            Events.query.delete()

            logging.info("Deleting data from CartItems...")
            CartItem.query.delete()

            logging.info("Deleting data from Carts...")
            Cart.query.delete()

            logging.info("Deleting data from Artworks...")
            Artwork.query.delete()

            logging.info("Deleting data from Users...")
            User.query.delete()

            logging.info("Deleting data from ShippingAddresses...")
            ShippingAddress.query.delete()

            db.session.commit()
            logging.info("Data deleted successfully.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting data: {e}")

def seed_users(num_users=10):
    with app.app_context():
        logging.info("Seeding users...")
        try:
            users = [User(username=fake.user_name(), email=fake.email(), password=fake.password(), role='user') for _ in range(num_users)]
            db.session.bulk_save_objects(users)
            db.session.commit()
            logging.info("Users seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error seeding users: {e}")

def seed_events():
    events_data = [
        # Your event data here...
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
        try:
            for event_data in events_data:
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
            db.session.commit()
            logging.info("Events seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error seeding events: {e}")

def seed_artworks():
    artworks_data = [
        {
        "title": "Starry Night",
        "description": "A masterpiece by Vincent van Gogh, depicting a dreamy view from the artist's asylum room.",
        "price": 1,
        "image": "https://i.ibb.co/484yd5n/Starry-night.jpg"
    },
    {
        "title": "Mona Lisa",
        "description": "A portrait of Lisa Gherardini, painted by Leonardo da Vinci.",
        "price": 1,
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
    },
    {
        "title": "Water Lilies",
        "description": "A series of approximately 250 oil paintings by Claude Monet, depicting his flower garden at Giverny.",
        "price": 8000000,
        "image": "https://i.ibb.co/zGc8Pmj/waterlilies.jpg"
    },
    {
        "title": "The Last Supper",
        "description": "A late 15th-century mural painting by Leonardo da Vinci, housed by the Convent of Santa Maria delle Grazie in Milan.",
        "price": 450000000,
        "image": "https://i.ibb.co/K27gBcW/The-Last-Supper.jpg"
    },
    {
        "title": "Liberty Leading the People",
        "description": "A painting by Eugène Delacroix commemorating the July Revolution of 1830 in France.",
        "price": 50000000,
        "image": "https://i.ibb.co/rfnFKXD/La-Libert-guidant.jpg"
    },
    {
        "title": "The Hay Wain",
        "description": "A painting by John Constable, showing a rural scene on the River Stour between the English counties of Suffolk and Essex.",
        "price": 10000000,
        "image": "https://i.ibb.co/7nKMrhx/The-Hay-Wain-1821.jpg"
    },
    {
        "title": "The Garden of Earthly Delights",
        "description": "A triptych by the Early Netherlandish painter Hieronymus Bosch, depicting the Garden of Eden and the Last Judgment.",
        "price": 80000000,
        "image": "https://i.ibb.co/9nZrC4G/The-Garden-of-earthly-delights.jpg"
    },
    {
        "title": "The School of Athens",
        "description": "A fresco by the Italian Renaissance artist Raphael, representing philosophy.",
        "price": 100000000,
        "image": "https://i.ibb.co/yFNzSsS/The-School-of-Athens-by-Raffaello-Sanzio-da-Urbino.jpg"
    },
    {
        "title": "The Wanderer above the Sea of Fog",
        "description": "An oil painting by German Romantic artist Caspar David Friedrich, depicting a man standing on a rocky promontory.",
        "price": 6000000,
        "image": "https://i.ibb.co/4W2x7XW/Wanderer-above-the-Sea-of-Fog.jpg"
    },
    {
        "title": "Las Meninas",
        "description": "A painting by Diego Velázquez, depicting the Infanta Margarita Teresa surrounded by her entourage.",
        "price": 200000000,
        "image": "https://i.ibb.co/zmjF5XM/Las-Meninas.jpg"
    },
    {
        "title": "Whistler's Mother",
        "description": "An 1871 painting by American-born artist James McNeill Whistler, depicting his mother, Anna McNeill Whistler.",
        "price": 35000000,
        "image": "https://i.ibb.co/k6ybRGc/Whistlers-Mother-high-res.jpg"
    },
    {
        "title": "A Sunday Afternoon on the Island of La Grande Jatte",
        "description": "A painting by Georges Seurat, depicting people relaxing in a suburban park on an island in the Seine River.",
        "price": 8000000,
        "image": "https://i.ibb.co/7rSCy8Q/sunday-afternoon.jpg"
    },
    {
        "title": "Nighthawks",
        "description": "A painting by Edward Hopper, portraying people in a downtown diner late at night.",
        "price": 9000000,
        "image": "https://i.ibb.co/3M8GQfT/nighthawk.jpg"
    },
    {
        "title": "The Night Café",
        "description": "An oil painting created by Dutch artist Vincent van Gogh in 1888, depicting a night café in Arles.",
        "price": 40000000,
        "image": "https://i.ibb.co/qg7YZBF/Vincent-Willem-van- Gogh-076.jpg"
    },
    {
        "title": "Impression, Sunrise",
        "description": "A painting by Claude Monet, which gave rise to the name of the Impressionist movement.",
        "price": 11000000,
        "image": "https://i.ibb.co/51xpFXY/impression-sunrise.jpg"
    },
    {
        "title": "The Gleaners",
        "description": "An oil painting by Jean-François Millet, depicting three peasant women gleaning a field of stray stalks of wheat after the harvest.",
        "price": 15000000,
        "image": "https://i.ibb.co/Ct49hym/Jean-Fran-ois-Millet.jpg"
    },
    {
        "title": "The Card Players",
        "description": "A series of oil paintings by the French Post-Impressionist artist Paul Cézanne.",
        "price": 250000000,
        "image": "https://i.ibb.co/mDrKMgB/260px-Les-Joueurs-de-cartes.jpg"
    },
    {
        "title": "Bal du moulin de la Galette",
        "description": "A painting by French artist Pierre-Auguste Renoir, portraying a typical Sunday afternoon at the original Moulin de la Galette in the district of Montmartre in Paris.",
        "price": 78000000,
        "image": "https://i.ibb.co/YT68J2v/1200px-Auguste-Renoir-Le-Moulin-de-la-Galette.jpg"
    },
        {
            "title": "Bal du moulin de la Galette",
            "description": "A painting by French artist Pierre-Auguste Renoir, portraying a typical Sunday afternoon at the original Moulin de la Galette in the district of Montmartre in Paris.",
            "price": 78000000,
            "image": "https://i.ibb.co/YT68J2v/1200px-Auguste-Renoir-Le-Moulin-de-la-Galette.jpg"
        },
        {
            "title": "Venus de Milo",
            "description": "An ancient Greek statue and one of the most famous works of ancient Greek sculpture, attributed to Alexandros of Antioch.",
            "price": 100000000,
            "image": "https://i.ibb.co/mTdTV0Q/Venus-de-Milo-Louvre-Ma-399-n2.jpg"
        },
        {
            "title": "The Thinker",
            "description": "A bronze sculpture by Auguste Rodin, representing a man in sober meditation battling with a powerful internal struggle.",
            "price": 14000000,
            "image": "https://i.ibb.co/FwM5Df1/The-Thinker-Auguste-Rodin-1904.jpg"
        }

    ]
    
    with app.app_context():
        logging.info("Seeding artworks...")
        try:
            for artwork_data in artworks_data:
                artwork = Artwork(
                    title=artwork_data["title"],
                    description=artwork_data["description"],
                    price=artwork_data["price"],
                    image=artwork_data["image"],
                    created_at=datetime.utcnow()
                )
                db.session.add(artwork)
            db.session.commit()
            logging.info("Artworks seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error seeding artworks: {e}")

def main():
    logging.info("Starting data seeding...")
    delete_existing_data()
    seed_users()
    seed_events()
    seed_artworks()
    logging.info("Data seeding completed.")

if __name__ == "__main__":
    main()