
import os
from datetime import datetime,date,time
from app import app, db
from models import Event, User, Booking, Ticket, Payment, Artwork,CartItem,OrderItem,Cart,Order
from faker import Faker
import logging


# Initialize Faker
fake = Faker()

# Set logging level
logging.basicConfig(level=logging.INFO)

def delete_existing_data():
    with app.app_context():
        logging.info("Deleting existing data...")
        CartItem.query.delete()
        Payment.query.delete()
        OrderItem.query.delete()
        Order.query.delete()
        Cart.query.delete()
        OrderItem.query.delete()
        Payment.query.delete()
        Booking.query.delete()
        Ticket.query.delete()
        Artwork.query.delete()
        Event.query.delete()
        User.query.delete()
        db.session.commit()



def seed_users():
    with app.app_context():
        logging.info("Seeding users...")

        # Define 10 fake users with predefined IDs
        predefined_users = [
            {"id": 1, "username": "user1", "email": "user1@example.com", "password": "password1", "role": "user"},
            {"id": 2, "username": "user2", "email": "user2@example.com", "password": "password2", "role": "user"},
            {"id": 3, "username": "user3", "email": "user3@example.com", "password": "password3", "role": "user"},
            {"id": 4, "username": "user4", "email": "user4@example.com", "password": "password4", "role": "user"},
            {"id": 5, "username": "user5", "email": "user5@example.com", "password": "password5", "role": "user"},
            {"id": 6, "username": "user6", "email": "user6@example.com", "password": "password6", "role": "user"},
            {"id": 7, "username": "user7", "email": "user7@example.com", "password": "password7", "role": "user"},
            {"id": 8, "username": "user8", "email": "user8@example.com", "password": "password8", "role": "user"},
            {"id": 9, "username": "user9", "email": "user9@example.com", "password": "password9", "role": "user"},
            {"id": 10, "username": "user10", "email": "user10@example.com", "password": "password10", "role": "user"}
        ]

        # Create User objects from the predefined user data
        users = [User(id=user["id"], username=user["username"], email=user["email"], password=user["password"], role=user["role"]) for user in predefined_users]

        # Clear existing users and insert predefined users
        db.session.query(User).delete()
        db.session.bulk_save_objects(users)
        db.session.commit()

        logging.info("Users seeded.")
        return predefined_users

def seed_events():
    events_data = [
    {
        "title": "The Grief Paintings",
        "image_url": "https://i.ibb.co/z8H2jLW/314974429fd5a0490f70a01b441a684c.jpg",
        "description": "An exhibition of new paintings by Helen Marden, created with resin, powdered pigment, ink, and natural objects, reflecting on life, love, and creativity.",
        "start_date": date(2024, 7, 24),
        "end_date": date(2024, 9, 14),
        "user_id": 1,
        "time": time(10, 0),
        "created_at": datetime.utcnow(),
        "location": "Gagosian 821 Park Avenue New York, NY USA",
    },
    {
        "title": "A Black Revolutionary Artist",
        "image_url": "https://i.ibb.co/nfSC3Tg/elizabeth-catlett-black-unity.jpg",
        "description": "Showcasing over 150 works by Elizabeth Catlett, this exhibition explores her career from DC to Mexico, highlighting her focus on social justice.",
        "start_date": date(2024, 9, 13),
        "end_date": date(2025, 1, 19),
        "user_id": 2,
        "time": time(20, 0),
        "created_at": datetime.utcnow(),
        "location": "Brooklyn Museum of Art",
    },
    {
        "title": "Summer Album",
        "image_url": "https://i.pinimg.com/474x/65/d4/6d/65d46d7471604b28b9a113a16326b69d.jpg",
        "description": "A curated collection capturing the essence and vibrancy of summer through diverse artworks.",
        "start_date": date(2024, 7, 26),
        "end_date": date(2024, 9, 7),
        "user_id": 3,
        "time": time(8, 0),
        "created_at": datetime.utcnow(),
        "location": "Ben Brown Fine Arts, Hong Kong China",
    },
    {
        "title": "Sculpting Dreams: Hands-On Sculpture Workshop",
        "image_url": "https://i.pinimg.com/474x/ca/50/26/ca50269e08f91b279490386227b9b6ff.jpg",
        "description": "A dynamic workshop for beginners to explore sculpture using mixed media.",
        "start_date": date(2024, 8, 12),
        "end_date": date(2024, 8, 15),
        "user_id": 4,
        "time": time(14, 0),
        "created_at": datetime.utcnow(),
        "location": "Art Center Studio, 123 Elm Street, Chicago, IL",
    },
    {
        "title": "Commemorations",
        "image_url": "https://i.pinimg.com/474x/d5/13/c1/d513c1d2bd93e1706c7ce99b2de83500.jpg",
        "description": "Joe Bloom’s solo exhibition featuring stained-glass orbs that symbolize light and tribute.",
        "start_date": date(2024, 8, 2),
        "end_date": date(2024, 9, 14),
        "user_id": 6,
        "time": time(10, 0),
        "created_at": datetime.utcnow(),
        "location": "Kristin Hjellegjerde Gallery, London",
    },
    {
        "title": "The Art of Light",
        "image_url": "https://i.pinimg.com/564x/db/b8/d1/dbb8d1891b6ae23b7a43a84e2afde81c.jpg",
        "description": "A showcase of light-based art from installations to interactive exhibits. The event highlights the role of light in art and features works that use illumination to create dynamic visual experiences.",
        "start_date": date(2024, 8, 15),
        "end_date": date(2024, 9, 30),
        "user_id": 3,
        "time": time(12, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Light Museum, Tokyo, Japan",
    },
    {
        "title": "Urban Rhythms",
        "image_url": "https://i.pinimg.com/474x/28/12/77/28127728ad85736f3362f3e8a7c6383b.jpg",
        "description": "Featuring works by street artists and muralists exploring urban life and culture. This exhibition captures the vibrancy and diversity of city environments through bold, colorful murals and street art.",
        "start_date": date(2024, 8, 20),
        "end_date": date(2024, 10, 1),
        "user_id": 3,
        "time": time(13, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "Street Art Gallery, Los Angeles, CA, USA",
    },
    {
        "title": "Abstract Realities",
        "image_url": "https://i.pinimg.com/474x/f8/44/4f/f8444fbea9bd1a6b4873817a2933b72e.jpg",
        "description": "An exhibition of abstract art that challenges perceptions of reality through innovative and diverse approaches. The show features works that use abstract forms to represent complex ideas and emotions.",
        "start_date": date(2024, 8, 25),
        "end_date": date(2024, 10, 10),
        "user_id": 2,
        "time": time(14, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "Tate Modern, London, UK",
    },
    {
        "title": "Ceramics Today",
        "image_url": "https://i.pinimg.com/474x/b1/06/55/b1065594dde69d261c666b3d2b34c3c5.jpg",
        "description": "A modern take on ceramic art, featuring both functional and sculptural pieces that push the boundaries of traditional ceramics. This exhibition highlights innovative techniques and contemporary designs in pottery and sculpture.",
        "start_date": date(2024, 9, 1),
        "end_date": date(2024, 10, 15),
        "user_id": 6,
        "time": time(10, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Ceramic Arts Museum, San Francisco, CA, USA",
    },
    {
        "title": "Echoes of the Past",
        "image_url": "https://i.pinimg.com/474x/81/bc/a0/81bca009afdef568fe294b5d7065ecd9.jpg",
        "description": "An exhibition blending historical and contemporary art to explore how past events and cultures influence modern artistic expressions. It features artworks that connect historical themes with current artistic practices.",
        "start_date": date(2024, 9, 5),
        "end_date": date(2024, 11, 5),
        "user_id": 5,
        "time": time(16, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "Rijksmuseum, Amsterdam, Netherlands"
    },
    {
        "title": "Women in Art",
        "image_url": "https://i.pinimg.com/474x/54/8d/82/548d82aa0ebb461a42af63c54119bb07.jpg",
        "description": "Celebrating the achievements of female artists across various eras and backgrounds. This exhibition highlights the contributions of women to the art world and examines their impact on artistic movements and styles.",
        "start_date": date(2024, 9, 10),
        "end_date": date(2024, 12, 10),
        "user_id": 6,
        "time": time(17, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "National Gallery of Art, Washington, D.C., USA"
    },
    {
        "title": "Digital Dreams",
        "image_url": "https://i.pinimg.com/736x/8f/90/ca/8f90ca0273702406caccfd2b267b921c.jpg",
        "description": "A look at how digital technology is transforming art through immersive and interactive experiences. The exhibition features virtual reality, augmented reality, and other digital art forms that challenge traditional boundaries.",
        "start_date": date(2024, 9, 15),
        "end_date": date(2024, 10, 30),
        "user_id": 5,
        "time": time(18, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Digital Art Museum, Seoul, South Korea"
    },
    {
        "title": "Timeless Forms",
        "image_url": "https://i.pinimg.com/474x/a2/ba/ab/a2baab3435ebe1ea12e79e9bd17c4089.jpg",
        "description": "Featuring classic and contemporary sculptures that challenge traditional forms. This exhibition showcases the evolution of sculpture and highlights works that explore form, function, and aesthetics.",
        "start_date": date(2024, 9, 20),
        "end_date": date(2024, 11, 1),
        "user_id": 4,
        "time": time(19, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Sculpture Center, New York, NY, USA"
    },
    {
        "title": "Cultural Threads",
        "image_url": "https://i.pinimg.com/474x/e7/52/54/e75254d904bfa8d881f8bf2c69f9180e.jpg",
        "description": "An exploration of textile art from different cultures around the world. The exhibition includes traditional and contemporary textile works that reflect cultural heritage, craftsmanship, and artistic expression.",
        "start_date": date(2024, 9, 25),
        "end_date": date(2024, 11, 15),
        "user_id": 3,
        "time": time(20, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "Textile Museum, Washington, D.C., USA"
    },
    {
        "title": "Reflections",
        "image_url": "https://images.pexels.com/photos/7976210/pexels-photo-7976210.jpeg?auto=compress&cs=tinysrgb&w=800",
        "description": "An exhibition focusing on art that incorporates reflective materials and explores themes of self-perception and introspection. The show features works that use mirrors, glass, and other reflective elements to create thought-provoking experiences.",
        "start_date": date(2024, 10, 1),
        "end_date": date(2024, 12, 1),
        "user_id": 2,
        "time": time(21, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Contemporary Museum, Sydney, Australia"
    },
    {
        "title": "The Modern Portrait",
        "image_url": "https://i.pinimg.com/474x/0c/f7/8a/0cf78a26f783b42e7cdafc0a0d350839.jpg",
        "description": "An exhibition showcasing innovative approaches to portraiture in the 21st century. The collection features contemporary portraits that reinterpret traditional techniques and explore new ways of representing identity and character.",
        "start_date": date(2024, 10, 5),
        "end_date": date(2024, 12, 15),
        "user_id": 1,
        "time": time(22, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "National Portrait Gallery, London, UK"
    },
    {
        "title": "Interactive Art",
        "image_url": "https://i.pinimg.com/474x/39/24/97/39249716a5c6a2fcc360eba0f42f09af.jpg",
        "description": "Art that engages viewers through interactive and participatory elements. This exhibition highlights artworks that require audience interaction to complete or enhance the artistic experience, blurring the line between art and viewer.",
        "start_date": date(2024, 10, 10),
        "end_date": date(2024, 11, 20),
        "user_id": 5,
        "time": time(23, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Interaction Museum, Los Angeles, CA, USA"
    },
    {
        "title": "Vivid Visions",
        "image_url": "https://images.pexels.com/photos/297394/pexels-photo-297394.jpeg?auto=compress&cs=tinysrgb&w=800",
        "description": "A showcase of artworks with vibrant colors and dynamic compositions that aim to captivate and inspire. The exhibition features artists known for their use of bold colors and energetic visual storytelling.",
        "start_date": date(2024, 10, 15),
        "end_date": date(2024, 12, 5),
        "user_id": 4,
        "time": time(10, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Modern Art Gallery, Tokyo, Japan"
    },
    {
        "title": "Metamorphosis",
        "image_url": "https://images.pexels.com/photos/2269667/pexels-photo-2269667.jpeg?auto=compress&cs=tinysrgb&w=800",
        "description": "Exploring art that depicts transformation and change across various media. This exhibition features works that illustrate the concept of metamorphosis in visual and conceptual forms.",
        "start_date": date(2024, 10, 20),
        "end_date": date(2024, 12, 10),
        "user_id": 6,
        "time": time(11, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "Art Institute of Chicago, IL, USA"
    },
    {
        "title": "Myth and Modernity",
        "image_url": "https://i.pinimg.com/474x/06/f1/0d/06f10dd95e9271b57c333b0b75d4e491.jpg",
        "description": "An exhibition blending mythological themes with contemporary art practices. The show features artworks that reinterpret classic myths and legends through modern artistic lenses.",
        "start_date": date(2024, 11, 1),
        "end_date": date(2025, 1, 15),
        "user_id": 2,
        "time": time(12, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Louvre, Paris, France"
    },
    {
        "title": "Sound and Vision",
        "image_url": "https://i.pinimg.com/474x/dd/11/a0/dd11a0a19f7d3b93984eb46fdfdfef83.jpg",
        "description": "Art that integrates sound and visual elements to create immersive experiences. This exhibition explores the intersection of audio and visual art, featuring works that combine these elements in innovative ways.",
        "start_date": date(2024, 11, 5),
        "end_date": date(2025, 1, 10),
        "user_id": 6,
        "time": time(13, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Museum of Sound Art, Berlin, Germany"
    },
    {
        "title": "Geometric Abstractions",
        "image_url": "https://i.pinimg.com/474x/0e/75/ff/0e75ff04c8c0d26681fa97cad74fc2b9.jpg",
        "description": "An exploration of geometric forms and abstract art in contemporary practice. The exhibition features artworks that use geometric shapes and abstraction to explore complex visual and conceptual themes.",
        "start_date": date(2024, 11, 10),
        "end_date": date(2025, 1, 5),
        "user_id": 6,
        "time": time(14, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Abstract Art Gallery, Milan, Italy"
    },
    {
        "title": "Whimsy and Wonder",
        "image_url": "https://i.pinimg.com/474x/5c/39/d8/5c39d84fb2b632ad09e73e541db9ca06.jpg",
        "description": "An exhibition of whimsical and fantastical artworks that inspire imagination and curiosity. Featuring dreamlike and surreal pieces, this show invites viewers to explore a world of creativity and wonder.",
        "start_date": date(2024, 11, 15),
        "end_date": date(2025, 1, 20),
        "user_id": 2,
        "time": time(15, 0),
        "created_at": datetime(2024, 8, 12),
        "location": "The Fantasy Art Museum, San Francisco, CA, USA"
    }
]
    
    with app.app_context():
        logging.info("Seeding events...")
        for event_data in events_data:
            try:
                start_date = datetime.strptime(event_data["start_date"], "%d-%m-%Y").date()
                end_date = datetime.strptime(event_data["end_date"], "%d-%m-%Y").date()
                event_time = datetime.strptime(event_data["time"], "%H:%M:%S").time()

                event = Event(
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

def seed_artworks():
    artworks_data = [
         {
        "title": "Sigma Art",
        "description": "As New Year 2015 begins, here are incredible Digital art and illustrations by professional artists and designers. The amazing illustration artwork that will.",
        "price": 1,
        'user_id': 1,
        "image": "https://i.pinimg.com/564x/4e/b1/c9/4eb1c9f1104ef8bb36967bd0d1b3c449.jpg"
    },
    {
        "title": "Colorful Beagle",
        "description": "Colorful Beagle illustration wearing sunglasses. With ink dripping from the bottom. This design is perfect for any Beagle dog lover.",
        "price": 1,
        'user_id': 2,
        "image": "https://i.pinimg.com/564x/0f/15/3d/0f153dde7df00dcbf8674f820eba855a.jpg"
    },
    {
        "title": "Inspiration Grid",
        "description": "Amsterdam-based art director Quentin Deronzier draws inspiration from the 80s visual aesthetic to create this spellbinding series of digital artwork",
        "price": 120000000,
        'user_id': 3,
        "image": "https://i.pinimg.com/564x/7a/b9/2d/7ab92dc75591dc8a86d045e0c1081c1a.jpg"
    },
    {
        "title": "The Maja",
        "description": "Graceful Flowery Collages  Fubiz Media",
        "price": 6000000,
        'user_id': 4,
        "image": "https://i.pinimg.com/236x/9c/c1/48/9cc148fe735288c77c6506c3a595fa49.jpg"
    },
    {
        "title": "Nature's Simplicity",
        "description": "Behold the minimalist elegance of nature in this singular artwork. With only two tones and flat shading, it celebrates the sheer simplicity of the natural world.",
        "price": 7000000,
        'user_id': 5,
        "image": "https://i.pinimg.com/564x/47/25/6a/47256ab8b281d7e4208443c4c2a252e2.jpg"
    },
    {
        "title": "The Night Watch",
        "description": "A painting by Rembrandt, portraying a group of trees.",
        "price": 45000000,
        'user_id': 6,
        "image": "https://i.pinimg.com/564x/52/bf/c2/52bfc20b0308f5b31bf1103fa2230bcc.jpg"
    },
    {
        "title": "The Natures Essence",
        "description": "An anti-war painting by Pablo Picasso, reflecting the bombing of Guernica.",
        "price": 200000000,
        'user_id':"https://i.pinimg.com/236x/0c/18/41/0c184144f417600378f2e5e9b9bff9f4.jpg"
    },
    {
        "title": "The Vibrant Hibiscus",
        "description": "A painting by Sandro Botticelli, depicting Venus emerging from the sea.",
        "price": 100000000,
        'user_id': 6,
        "image": "https://i.pinimg.com/236x/47/8d/4f/478d4f22a0d7ab798f4394af7c93cf62.jpg"
    },
    {
        "title": "The Kiss",
        "description": "A painting by Gustav Klimt, representing an intimate embrace.",
        "price": 150000000,
        'user_id': 5,
        "image": "https://i.pinimg.com/564x/f1/34/07/f13407656ee72abc7461823449d4423d.jpg"
    },
    {
        "title": "America Colorful",
        "description": "A painting by Grant Wood, showing a farmer and his daughter.",
        "price": 30000000,
        'user_id': 4,
        "image": "https://i.pinimg.com/564x/ba/3b/60/ba3b6075fd2d5340341f5f0d07188d5c.jpg"
    },
    {
        "title": "The Arnolfini Portrait",
        "description": "A painting by Jan van Eyck, featuring a double portrait of Giovanni di Nicolao di Arnolfini and his wife.",
        "price": 20000000,
        'user_id': 3,
        "image": "https://i.ibb.co/ZjvTs9J/Arnolfini-Portrait.jpg"
    },
    {
        "title": "Water Lilies",
        "description": "A series of approximately 250 oil paintings by Claude Monet, depicting his flower garden at Giverny.",
        "price": 8000000,
        'user_id': 2,
        "image": "https://i.ibb.co/zGc8Pmj/waterlilies.jpg"
    },
    {
        "title": "The Last Supper",
        "description": "A late 15th-century mural painting by Leonardo da Vinci, housed by the Convent of Santa Maria delle Grazie in Milan.",
        "price": 450000000,
        'user_id': 2,
        "image": "https://i.pinimg.com/564x/b4/e9/8b/b4e98bb1f24707e8e3fddb1698267b24.jpg"
    },
    {
        "title": "Liberty Leading the People",
        "description": "A painting by Eugène Delacroix commemorating the July Revolution of 1830 in France.",
        "price": 50000000,
        'user_id': 2,
        "image": "https://i.ibb.co/rfnFKXD/La-Libert-guidant.jpg"
    },
    {
        "title": "The Hay Wain",
        "description": "A painting by John Constable, showing a rural scene on the River Stour between the English counties of Suffolk and Essex.",
        "price": 10000000,
        'user_id': 3,
        "image": "https://i.ibb.co/7nKMrhx/The-Hay-Wain-1821.jpg"
    },
    {
        "title": "The Garden of Earthly Delights",
        "description": "A triptych by the Early Netherlandish painter Hieronymus Bosch, depicting the Garden of Eden and the Last Judgment.",
        "price": 80000000,
        'user_id': 3,
        "image": "https://i.ibb.co/9nZrC4G/The-Garden-of-earthly-delights.jpg"
    },
    {
        "title": "The School of Athens",
        "description": "A fresco by the Italian Renaissance artist Raphael, representing philosophy.",
        "price": 100000000,
        'user_id': 3,
        "image": "https://i.ibb.co/yFNzSsS/The-School-of-Athens-by-Raffaello-Sanzio-da-Urbino.jpg"
    },
    {
        "title": "The Wanderer above the Sea of Fog",
        "description": "An oil painting by German Romantic artist Caspar David Friedrich, depicting a man standing on a rocky promontory.",
        "price": 6000000,
        'user_id': 2,
        "image": "https://i.ibb.co/4W2x7XW/Wanderer-above-the-Sea-of-Fog.jpg"
    },
    {
        "title": "Las Meninas",
        "description": "A painting by Diego Velázquez, depicting the Infanta Margarita Teresa surrounded by her entourage.",
        "price": 200000000,
        'user_id': 3,
        "image": "https://i.ibb.co/zmjF5XM/Las-Meninas.jpg"
    },
    {
        "title": "Whistler's Mother",
        "description": "An 1871 painting by American-born artist James McNeill Whistler, depicting his mother, Anna McNeill Whistler.",
        "price": 35000000,
        'user_id': 3,
        "image": "https://i.ibb.co/k6ybRGc/Whistlers-Mother-high-res.jpg"
    },
    {
        "title": "A Sunday Afternoon on the Island of La Grande Jatte",
        "description": "A painting by Georges Seurat, depicting people relaxing in a suburban park on an island in the Seine River.",
        "price": 8000000,
        'user_id': 1,
        "image": "https://i.ibb.co/7rSCy8Q/sunday-afternoon.jpg"
    },
    {
        "title": "Nighthawks",
        "description": "A painting by Edward Hopper, portraying people in a downtown diner late at night.",
        "price": 9000000,
        'user_id': 1,
        "image": "https://i.ibb.co/3M8GQfT/nighthawk.jpg"
    },
    {
        "title": "The Night Café",
        "description": "An oil painting created by Dutch artist Vincent van Gogh in 1888, depicting a night café in Arles.",
        "price": 40000000,
        'user_id': 1,
        "image": "https://i.ibb.co/qg7YZBF/Vincent-Willem-van- Gogh-076.jpg"
    },
    {
        "title": "Furry Red",
        "description": "Welcome to my humble corner of creativity! I am thrilled to present to you a meticulously crafted cross stitch pattern that combines the timeless art of cross stitching with the beauty of AI artwork",
        "price": 11000,
        'user_id': 1,
        "image": "https://i.pinimg.com/236x/e1/08/ec/e108ec065fb164848df889f64e404567.jpg"
    },
    {
        "title": "Collage Art",
        "description": "The standing appointment of our blog, that contains a mix of the best graphics & all other design fields artworks, to find inspiration for a new creative week!.",
        "price": 15000,
        'user_id': 1,
        "image": "https://i.pinimg.com/236x/a7/4f/d2/a74fd2a1349cb883c81e692f0c88d41d.jpg"
    },
    {
        "title": "The Modern Stitch",
        "description": "The pattern includes a grand total of 41,280 stitches, a testament to the dedication and passion poured into its creation. .",
        "price": 25000,
        'user_id': 1,
        "image": "https://i.pinimg.com/236x/61/45/5c/61455c6a10b9d47f6317b19154d7fae2.jpg"
    },
    {
        "title": "Geisha Artwork",
        "description": "The tree leaves are rendered in shades of red, green and white, creating a sense of warmth and vitality. The mountains are rendered in shades of white and grey, creating a sense of elegance and grandeur",
        "price": 7800,
        'user_id': 1,
        "image": "https://i.pinimg.com/236x/95/b4/4a/95b44a3fba637882e7ee0685c5c52de3.jpg"
    },
        {
            "title": "Women Digital Art",
            "description": "The women digital artwork ships in a tube directly from the artist's studio , so you can buy with confidence.",
            "price": 7800,
            'user_id': 1,
            "image": "https://i.pinimg.com/736x/d4/f0/b1/d4f0b1c437c58f484f640435b78e5d40.jpg"
        },
        {
            "title": "Contemporary Dance Art",
            "description": "Minimalistic Oil Painting Of An Elegant Woman Performing Contemporary Dance In A Beautifully Adorned Ballroom Lit By Orange Candles.. Displate is a one-of-a-kind metal poster designed to capture your unique passions. Sturdy, magnet mounted, and durable – not to mention easy on the eyes!",
            "price": 10000,
            'user_id': 1,
            "image": "https://i.pinimg.com/736x/1b/0c/a0/1b0ca0e42306066c0ed1d6cdcd8aec35.jpg"
        },
        {
            "title": "The Thinker",
            "description": "A bronze sculpture by Auguste Rodin, representing a man in sober meditation battling with a powerful internal struggle.",
            "price": 14000,
            'user_id': 1,
            "image": "https://i.pinimg.com/236x/6d/ea/3f/6dea3ff46eef9cffe000280f7c683db4.jpg"
        }

    ]
    
    with app.app_context():
        logging.info("Seeding artworks...")
        for artwork_data in artworks_data:
            try:
                artwork = Artwork(
                    title=artwork_data["title"],
                    description=artwork_data["description"],
                    price=artwork_data["price"],
                    image=artwork_data["image"],
                    created_at=datetime.utcnow()
                )
                db.session.add(artwork)
            except Exception as e:
                logging.error(f"Error adding Artwork {artworks_data['title']}: {e}")

        try:
            db.session.commit()
            logging.info("Artworks seeded.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing to database: {e}")
            
            
            
            
def create_ticket_data():
    with app.app_context():
        # Fetch the first 23 events
        events = Event.query.limit(23).all()

        if not events:
            print("No events found in the database.")
            return

        # Define ticket data for each event
        ticket_data = [
            # Event 1 tickets
            {
                'event_id': events[0].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 100, 'quantity': 200},
                    {'type_name': 'VIP', 'price': 200, 'quantity': 100},
                    {'type_name': 'VVIP', 'price': 300, 'quantity': 50},
                ]
            },
            # Event 2 tickets
            {
                'event_id': events[1].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 120, 'quantity': 180},
                    {'type_name': 'VIP', 'price': 220, 'quantity': 90},
                    {'type_name': 'VVIP', 'price': 320, 'quantity': 40},
                ]
            },
            # Event 3 tickets
            {
                'event_id': events[2].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 110, 'quantity': 210},
                    {'type_name': 'VIP', 'price': 210, 'quantity': 110},
                    {'type_name': 'VVIP', 'price': 310, 'quantity': 60},
                ]
            },
            # Event 4 tickets
            {
                'event_id': events[3].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 130, 'quantity': 170},
                    {'type_name': 'VIP', 'price': 230, 'quantity': 80},
                    {'type_name': 'VVIP', 'price': 330, 'quantity': 30},
                ]
            },
            # Event 5 tickets
            {
                'event_id': events[4].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 140, 'quantity': 160},
                    {'type_name': 'VIP', 'price': 240, 'quantity': 70},
                    {'type_name': 'VVIP', 'price': 340, 'quantity': 20},
                ]
            },
            # Event 6 tickets
            {
                'event_id': events[5].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 150, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 450, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 550, 'quantity': 10},
                ]
            },
            # Event 7 tickets
            {
                'event_id': events[6].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 180, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 290, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 360, 'quantity': 10},
                ]
            },
            # Event 8 tickets
            {
                'event_id': events[7].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 150, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 350, 'quantity': 10},
                ]
            },
            # Event 9 tickets
            {
                'event_id': events[8].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 150, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 350, 'quantity': 10},
                ]
            },
            # Event 10 tickets
            {
                'event_id': events[9].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 650, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 950, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 1050, 'quantity': 10},
                ]
            },
            # Event 11 tickets
            {
                'event_id': events[10].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 350, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 550, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 950, 'quantity': 10},
                ]
            },
            # Event 12 tickets
            {
                'event_id': events[11].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 20, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 25, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 35, 'quantity': 10},
                ]
            },
            # Event 13 tickets
            {
                'event_id': events[12].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 130, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 370, 'quantity': 10},
                ]
            },
            # Event 14 tickets
            {
                'event_id': events[13].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 150, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 300, 'quantity': 10},
                ]
            },
            # Event 15 tickets
            {
                'event_id': events[14].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 150, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 200, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 350, 'quantity': 10},
                ]
            },
            # Event 16 tickets
            {
                'event_id': events[15].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 100, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 350, 'quantity': 10},
                ]
            },
            # Event 17 tickets
            {
                'event_id': events[16].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 158, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 200, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 305, 'quantity': 10},
                ]
            },
            # Event 18 tickets
            {
                'event_id': events[17].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 15, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 25, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 35, 'quantity': 10},
                ]
            },
            # Event 19 tickets
            {
                'event_id': events[18].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 750, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 850, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 1050, 'quantity': 10},
                ]
            },
            # Event 20 tickets
            {
                'event_id': events[19].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 250, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 350, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 450, 'quantity': 10},
                ]
            },
            # Event 21 tickets
            {
                'event_id': events[20].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 190, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 260, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 850, 'quantity': 10},
                ]
            },
            # Event 22 tickets
            {
                'event_id': events[21].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 50, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 250, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 350, 'quantity': 10},
                ]
            },
            # Event 23 tickets
            {
                'event_id': events[22].id,
                'tickets': [
                    {'type_name': 'Regular', 'price': 140, 'quantity': 150},
                    {'type_name': 'VIP', 'price': 240, 'quantity': 60},
                    {'type_name': 'VVIP', 'price': 340, 'quantity': 10},
                ]
            }
        ]

        try:
            # Create ticket objects and save them to the database
            for data in ticket_data:
                event_id = data['event_id']
                for ticket_info in data['tickets']:
                    ticket = Ticket(
                        type_name=ticket_info['type_name'],
                        price=ticket_info['price'],
                        quantity=ticket_info['quantity'],
                        event_id=event_id
                    )
                    db.session.add(ticket)
            
            # Commit the changes to the database
            db.session.commit()
            print("Tickets created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred while creating tickets: {e}")
        
            

def main():
    logging.info("Starting data seeding...")
    delete_existing_data()
    seed_users()
    seed_events()
    seed_artworks()
    logging.info("Data seeding completed.")

if __name__ == "__main__":
    main()
    create_ticket_data()
    
    
    