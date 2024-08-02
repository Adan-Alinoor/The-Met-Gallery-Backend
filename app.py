from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restful import Resource, Api
from models import db, User, Product, Cart, CartItem

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


class AddToCartResource(Resource):
    def post(self):
        data = request.get_json()

        # Find or create user (assuming a user is authenticated and user_id is available)
        user_id = data.get('user_id')  # Adjust this line as per your authentication system
        if not user_id:
            return {'error': 'User ID is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find or create cart for the user
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()

        # Check if product exists
        product = Product.query.get(data['product_id'])
        if not product:
            return {'error': 'Product not found'}, 404

        # Get the quantity to add
        quantity = data.get('quantity', 1)  # Default to 1 if quantity is not provided

        # Check if the product is already in the cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        if cart_item:
            # Update the quantity if the product is already in the cart
            cart_item.quantity += quantity  # Adjust quantity increment as needed
        else:
            # Add new CartItem if the product is not in the cart
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity, # Adjust quantity as needed
                name = product.name,
                description=product.description,
                price=product.price,
                image=product.image
            )
            db.session.add(cart_item)

        db.session.commit()

        return {'message': 'Product added to cart'}, 201


class RemoveFromCartResource(Resource):
    def post(self):
        data = request.get_json()

        # Find or create user (assuming a user is authenticated and user_id is available)
        user_id = data.get('user_id')  # Adjust this line as per your authentication system
        product_id = data.get('product_id')
        if not user_id or not product_id:
            return {'error': 'User ID and Product ID are required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        # Find the user's cart
        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart:
            return {'error': 'Cart not found'}, 404

        # Find the CartItem to be removed
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if not cart_item:
            return {'error': 'Product not found in cart'}, 404

        # Decrement the quantity or remove the CartItem
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)

        db.session.commit()

        return {'message': 'Product removed from cart'}, 200


class ViewCartResource(Resource):
    def get(self, user_id):
        # Find the user's cart
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return {"error": "Cart not found"}, 404

        # Fetch all cart items
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return {"message": "Cart is empty"}, 200

        # Convert cart items to dictionary format
        cart_items_list = [item.to_dict() for item in cart_items]
        return {'items': cart_items_list}, 200


api.add_resource(AddToCartResource, '/add_to_cart')
api.add_resource(RemoveFromCartResource, '/remove_from_cart')
api.add_resource(ViewCartResource, '/view_cart/<int:user_id>')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5555)
