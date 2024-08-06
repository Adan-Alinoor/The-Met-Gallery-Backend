from models import db, User, Product
from app import app
from faker import Faker
import logging

# Initialize Faker
fake = Faker()

# Set logging level for specific modules or hand
logging.basicConfig(level=logging.INFO)

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

def seed_products():
    Product.query.delete()
    
    artworks = [
        {
            "title": "Starry Night",
            "description": "A masterpiece by Vincent van Gogh, depicting a dreamy interpretation of the artist's asylum room's sweeping view of Saint-Rémy-de-Provence at night.",
            "price": 5000000,
            "image": "https://i.ibb.co/484yd5n/Starry-night.jpg"
        },
        {
            "title": "Mona Lisa",
            "description": "A portrait of Lisa Gherardini, wife of Francesco del Giocondo, known as the Mona Lisa, painted by Leonardo da Vinci.",
            "price": 2,
            "image": "https://i.ibb.co/yQDhv3z/monalisa.jpg"
        },
        {
            "title": "The Scream",
            "description": "An iconic work by Norwegian artist Edvard Munch, symbolizing the anxiety of the human condition.",
            "price": 120000000,
            "image": "https://i.ibb.co/PMhrqp2/the-scream.jpg"
        },
        {
            "title": "The Persistence of Memory",
            "description": "A surreal painting by Salvador Dalí, showcasing melting clocks in a desert landscape.",
            "price": 6000000,
            "image": "https://i.ibb.co/kHxK6FV/The-Persistence-of-Memory.jpg"
        },
        {
            "title": "Girl with a Pearl Earring",
            "description": "An oil painting by Dutch Golden Age painter Johannes Vermeer, depicting a girl wearing a pearl earring.",
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
            "description": "A powerful anti-war painting by Pablo Picasso, reflecting the bombing of Guernica during the Spanish Civil War.",
            "price": 200000000,
            "image": "https://i.ibb.co/gVB8SQK/Picasso-Guernica.jpg"
        },
        {
            "title": "The Birth of Venus",
            "description": "A painting by Sandro Botticelli, depicting the goddess Venus emerging from the sea.",
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
            "description": "A painting by Grant Wood, showing a farmer and his daughter standing in front of a house.",
            "price": 30000000,
            "image": "https://i.ibb.co/5xMc8zq/American-Gothic.jpg"
        },
        {
            "title": "The Arnolfini Portrait",
            "description": "A painting by Jan van Eyck, depicting Giovanni di Nicolao di Arnolfini and his wife.",
            "price": 90000000,
            "image": "https://i.ibb.co/2ZcxBQx/Arnolfini-Portrait.png"
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
    
    for artwork in artworks:
        product = Product(
            name=artwork['title'],
            description=artwork['description'],
            price=artwork['price'],
            image=artwork['image']
        )
        db.session.add(product)
    db.session.commit()


def seed_all():
    with app.app_context():
        seed_users()
        seed_products()
      

if __name__ == '__main__':
    seed_all()
