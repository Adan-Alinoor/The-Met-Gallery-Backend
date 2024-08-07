import os
from datetime import datetime
from app import app, db
from models import Events, User, Booking, Ticket, Payment
from faker import Faker

with app.app_context():
    fake = Faker()

def delete_existing_data():
    # This will delete any existing rows
    # so you can run the seed file multiple times without having duplicate entries in your database
    with app.app_context():
        print("Deleting data...")
        Events.query.delete()
        User.query.delete()
        Booking.query.delete()
        Ticket.query.delete()
        Payment.query.delete()

def seed_users():
    with app.app_context():
        # Create and add fake users
        users = []
        for _ in range(10):  # Generate 10 fake users
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                password=fake.password(),
                role='user'  # You can modify the role as needed
            )
            users.append(user)
        
        db.session.bulk_save_objects(users)
        db.session.commit()

events_data = [
    {
        "title": "The Grief Paintings",
        "image_url": "https://images.artnet.com/gallery-images/425937671/95826851-8e2f-4dbe-a10d-e9c97c1b7997.jpg?x=1320%40%211320aD0xMzIwJnc9MTMyMCZmPWNvbnRhaW4mdD1s",
        "description": "An exhibition of new paintings by Helen Marden. Begun in 2023 as Marden cared for her husband, Brice, and made over the months following his passing, the Grief Paintings are intimately scaled abstractions created with resin, powdered pigment, ink, and natural objects. Flowing layers of vivid color and assemblages of feathers, shells, and sea glass extend beyond the paintings’ circular supports. Imbued with the spirit of life, love, and creativity, this body of work takes on new meaning in accord with the poem “Growing Up in America” by Rene Ricard, a longtime friend of the couple.",
        "start_date": "24-07-2024",
        "end_date": "14-09-2024",
        "user_id": 1,
        "time": "10:00:00",
        "location": "Gagosian 821 Park Avenue New York, NY USA"
    },
    {
        "title": "A Black Revolutionary Artist",
        "image_url": "https://www.nga.gov/content/dam/ngaweb/exhibitions/promos/2025/elizabeth-catlett-black-unity.jpg",
        "description": "Committed to both craft and causes, Elizabeth Catlett, a defining artist of the 20th century, addressed injustices in America and Mexico through her bold prints and dynamic sculptures. This exhibition showcases over 150 of her works, including rarely seen paintings and drawings, tracing her career from her roots in DC, Chicago, and New York to her 60-year legacy in Mexico. Catlett’s art centers on social justice, making it accessible and impactful for all.",
        "start_date": "13-09-2024",
        "end_date": "19-01-2025",
        "user_id": 2,
        "time": "20:00:00",
        "location": "Brooklyn Museum of Art"
    },
    {
        "title": "Summer Album",
        "image_url": "https://images.artnet.com/gallery-images/424675664/5e88ef11-6277-4c47-98db-de80afa8d678.jpg?x=1320%40%211320aD0xMzIwJnc9MTMyMCZmPWNvbnRhaW4mdD1s",
        "description": "The Summer Album features a curated collection of artworks that capture the essence and vibrancy of the summer season. Expect a diverse range of pieces showcasing bright colors, dynamic compositions, and themes related to warmth, nature, and leisure. The album is designed to evoke the feelings and experiences associated with summer, offering an immersive visual experience that reflects the lively and relaxed spirit of the season.",
        "start_date": "26-07-2024",
        "end_date": "07-09-2024",
        "user_id": 3,
        "time": "08:00:00",
        "location": "Ben Brown Fine Arts, Hong Kong China"
    },
    {   
        "title": "Sculpting Dreams: Hands-On Sculpture Workshop",
        "image_url": "https://i.pinimg.com/474x/ca/50/26/ca50269e08f91b279490386227b9b6ff.jpg",
        "description": "Unleash your creativity at 'Sculpting Dreams,' a dynamic workshop designed for beginners eager to explore the world of sculpture. Under the guidance of talented instructors, learn to shape abstract forms using mixed media. Perfect for aspiring sculptors and art lovers looking to create something truly unique.",
        "start_date": "12-08-2024",
        "end_date": "15-08-2024",
        "user_id": 4,
        "time": "14:00:00",
        "location": "Art Center Studio, 123 Elm Street, Chicago, IL"
    },
    {
        "title": "Frühe Grafik",
        "image_url": "https://images.artnet.com/gallery-images/115607/1638779.jpg?x=%40%21614xiu8%5EaD0mdz02MTQmZj1jb250YWluJnQ9bA%3D%3D",
        "description": "Explore the origins of Swiss modern art with Bernhard Luginbühl: Frühe Grafik. This compelling exhibition unveils Luginbühl's early graphic works, revealing the intricate lines and bold forms that laid the groundwork for his acclaimed sculptures. Dive into the foundation of his artistic vision and experience the innovation that defined his career. Don’t miss this chance to discover the early genius of a master artist.",
        "start_date": "05-09-2024",
        "end_date": "01-11-2024",
        "user_id": 5,
        "time": "12:00:00",
        "location": "Galerie Ziegler, Switzerland"
    },
    {
        "title": "Commemorations",
        "image_url": "https://images.artnet.com/gallery-images/115607/1638779.jpg?x=%40%21614xiu8%5EaD0mdz02MTQmZj1jb250YWluJnQ9bA%3D%3D",
        "description": "Commemorations at Kristin Hjellegjerde Gallery showcases Joe Bloom’s debut solo exhibition featuring stained-glass orbs that symbolize both light and tribute. His new series blends intricate detail with dynamic color to explore how we memorialize events and moments. Each painting, such as 'A Fruitless Bounty?', invites viewers to engage with themes of fragility, irony, and personal narrative. Discover Bloom's evocative works that challenge and reflect on our understanding of commemoration.",
        "start_date": "02-08-2024",
        "end_date": "14-09-2024",
        "user_id": 6,
        "time": "10:00:00",
        "location": "Kristin Hjellegjerde Gallery, London"
    }
]

def seed_events():
    with app.app_context():
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
                print(f"Error adding event {event_data['title']}: {e}")

        try:
            db.session.commit()
            print("Seeding completed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to database: {e}")

if __name__ == "__main__":
    delete_existing_data()  # Call to delete existing data
    seed_users()            # Seed the users
    seed_events()          # Seed the events
