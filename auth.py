
from functools import wraps
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import User


def user_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return {'error': 'Admin access required'}, 403
        return fn(*args, **kwargs)
    return wrapper

def admin_or_seller_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or (not user.is_admin and not user.is_seller):
            return {'error': 'Admin or seller access required'}, 403
        return fn(*args, **kwargs)
    return wrapper


'''

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

        # Check if artwork exists
        artwork = Artwork.query.get(data['artwork_id'])
        if not artwork:
            return {'error': 'artwork not found'}, 404

        
        quantity = data.get('quantity', 1)  
        
        cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork.id).first()
        if cart_item:
            # Update the quantity if the artwork is already in the cart
            cart_item.quantity += quantity  # Adjust quantity increment as needed
        else:
            # Add new CartItem if the artwork is not in the cart
            cart_item = CartItem(
                cart_id=cart.id,
                artwork_id=artwork.id,
                quantity=quantity, # Adjust quantity as needed
                title = artwork.title,
                description=artwork.description,
                price=artwork.price,
                image=artwork.image
            )
            db.session.add(cart_item)

        db.session.commit()

        return {'message': 'Artwork added to cart'}, 201


# class RemoveFromCartResource(Resource):
#     def post(self):
#         data = request.get_json()

#         # Find or create user (assuming a user is authenticated and user_id is available)
#         user_id = data.get('user_id')  # Adjust this line as per your authentication system
#         artwork_id = data.get('artwork_id')
#         if not user_id or not artwork_id:
#             return {'error': 'User ID and artwork ID are required'}, 400

#         user = User.query.get(user_id)
#         if not user:
#             return {'error': 'User not found'}, 404

#         # Find the user's cart
#         cart = Cart.query.filter_by(user_id=user.id).first()
#         if not cart:
#             return {'error': 'Cart not found'}, 404

#         # Find the CartItem to be removed
#         cart_item = CartItem.query.filter_by(cart_id=cart.id, artwork_id=artwork_id).first()
#         if not cart_item:
#             return {'error': 'Artwork not found in cart'}, 404

#         # Decrement the quantity or remove the CartItem
#         if cart_item.quantity > 1:
#             cart_item.quantity -= 1
#         else:
#             db.session.delete(cart_item)

#         db.session.commit()

#         return {'message': 'Artwork removed from cart'}, 200


# class ViewCartResource(Resource):
#     def get(self, user_id):
#         # Find the user's cart
#         cart = Cart.query.filter_by(user_id=user_id).first()
#         if not cart:
#             return {"error": "Cart not found"}, 404

#         # Fetch all cart items
#         cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
#         if not cart_items:
#             return {"message": "Cart is empty"}, 200

#         # Convert cart items to dictionary format
#         cart_items_list = [item.to_dict() for item in cart_items]
#         return {'items': cart_items_list}, 200


'''