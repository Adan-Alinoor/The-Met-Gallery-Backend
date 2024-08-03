from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Artwork

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


class ArtworkListResource(Resource):
    def get(self):
        try:
            artworks = Artwork.query.all()
            return [artwork.to_dict() for artwork in artworks], 200
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self):
        data = request.get_json()
        if not data:
            return {"error": "No input data provided"}, 400
        if not all(k in data for k in ("title", "description", "price", "image")):
            return {"error": "Missing fields in input data"}, 400

        try:
            new_artwork = Artwork(
                title=data['title'],
                description=data['description'],
                price=data['price'],
                image=data['image']
            )
            db.session.add(new_artwork)
            db.session.commit()
            return {"message": "Artwork created", "artwork": new_artwork.to_dict()}, 201
        except Exception as e:
            return {"error": str(e)}, 500


class ArtworkResource(Resource):
    def get(self, id):
        try:
            artwork = Artwork.query.get_or_404(id)
            return artwork.to_dict(), 200
        except Exception as e:
            return {"error": str(e)}, 500

    def put(self, id):
        data = request.get_json()
        if not data:
            return {"error": "No input data provided"}, 400

        try:
            artwork = Artwork.query.get_or_404(id)
            artwork.title = data.get('title', artwork.title)
            artwork.description = data.get('description', artwork.description)
            artwork.price = data.get('price', artwork.price)
            artwork.image = data.get('image', artwork.image)
            db.session.commit()
            return {"message": "Artwork updated", "artwork": artwork.to_dict()}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    def delete(self, id):
        try:
            artwork = Artwork.query.get_or_404(id)
            db.session.delete(artwork)
            db.session.commit()
            return {"message": "Artwork deleted"}, 200
        except Exception as e:
            return {"error": str(e)}, 500


api.add_resource(ArtworkListResource, '/artworks')
api.add_resource(ArtworkResource, '/artworks/<int:id>')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5555)
