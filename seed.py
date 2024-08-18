from faker import Faker
from random import randint, choice
from datetime import datetime, timedelta
from app import app, db  # Adjust the import according to your app structure
from models import User, Event, Artwork, Ticket
from sqlalchemy.sql import text
import requests
from dotenv import load_dotenv
import os

fake = Faker()
load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')


def fetch_image_url(query):
    response = requests.get('https://api.unsplash.com/photos/random', params={
        'query': query,
        'client_id': UNSPLASH_ACCESS_KEY,
        'count': 50  
    })

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    try:
        data = response.json()
        if data:
            return data[0]['urls']['regular']
    except ValueError:
        print("Error decoding JSON response.")

    return 'https://images.unsplash.com/photo-1580195319388-1bea55742a42?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTh8fGFydCUyMGdhbGxlcnl8ZW58MHx8MHx8fDA%3D'  # Fallback image

def create_users(num_users):
    users = []
    for _ in range(num_users):
        try:
            username = fake.user_name()
            email = fake.email()
            password = fake.password()
            role = choice(['user', 'admin'])
            is_admin = role == 'admin'
            is_seller = role == 'user'
            
            user = User(
                username=username,
                email=email,
                password=password,
                role=role,
                is_admin=is_admin,
                is_seller=is_seller
            )
            users.append(user)
        except Exception as e:
            print(f"Error creating user: {e}")
    return users

def create_events(users, num_events):
    events = []
    for _ in range(num_events):
        title = fake.sentence(nb_words=3)
        image_url = fetch_image_url('art gallery')
        description = fake.text(max_nb_chars=400)
        start_date = fake.date_between(start_date='today', end_date='+1y')
        end_date = start_date + timedelta(days=randint(1, 10))
        user_id = choice([user.id for user in users])
        time = fake.time()
        location = fake.address()

        event = Event(
            title=title,
            image_url=image_url,
            description=description,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            time=time,
            location=location
        )
        events.append(event)
    return events

def create_artworks(num_artworks):
    artworks = []
    for _ in range(num_artworks):
        title = fake.word()
        description = fake.text(max_nb_chars=400)
        price = randint(100, 10000)
        image = fetch_image_url('art')

        artwork = Artwork(
            title=title,
            description=description,
            price=price,
            image=image
        )
        artworks.append(artwork)
    return artworks

def create_tickets(events):
    tickets = []
    ticket_types = ['Regular', 'VIP', 'VVIP']
    for event in events:
        for type_name in ticket_types:
            price = randint(50, 500)
            quantity = randint(100, 1000)

            ticket = Ticket(
                event_id=event.id,
                type_name=type_name,
                price=price,
                quantity=quantity
            )
            tickets.append(ticket)
    return tickets

def seed_data():
    with app.app_context():
        # Clear existing data
        db.session.execute(text('TRUNCATE TABLE events, artworks, tickets RESTART IDENTITY CASCADE'))
        db.session.commit()

        # Create and add data
        users = create_users(5)
        db.session.add_all(users)
        db.session.commit()

        events = create_events(users, 30)
        db.session.add_all(events)
        db.session.commit()

        artworks = create_artworks(20)
        db.session.add_all(artworks)
        db.session.commit()

        tickets = create_tickets(events)
        db.session.add_all(tickets)
        db.session.commit()

        print('Data seeded successfully!')

if __name__ == '__main__':
    seed_data()
