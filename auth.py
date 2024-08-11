
# from functools import wraps
# from flask_jwt_extended import get_jwt_identity, jwt_required
# from models import User


# def user_required(fn):
#     @wraps(fn)
#     @jwt_required()
#     def wrapper(*args, **kwargs):
#         user_id = get_jwt_identity()
#         user = User.query.get(user_id)
#         if not user:
#             return {'message': 'User not found'}, 404
#         return fn(*args, **kwargs)
#     return wrapper

# # def admin_required(fn):
# #     @wraps(fn)
# #     @jwt_required()
# #     def wrapper(*args, **kwargs):
# #         user_id = get_jwt_identity()
# #         user = User.query.get(user_id)
# #         if not user or not user.is_admin:
# #             return {'error': 'Admin access required'}, 403
# #         return fn(*args, **kwargs)
# #     return wrapper


# def admin_required(fn):
#     @wraps(fn)
#     @jwt_required()
#     def wrapper(*args, **kwargs):
#         user_id = get_jwt_identity()
#         user = User.query.get(user_id)
#         if not user or not user.is_admin:
#             return {'error': 'Admin access required'}, 403
#         return fn(*args, **kwargs)
#     return wrapper

# def admin_or_seller_required(fn):
#     @wraps(fn)
#     @jwt_required()
#     def wrapper(*args, **kwargs):
#         user_id = get_jwt_identity()
#         user = User.query.get(user_id)
#         if not user or (not user.is_admin and not user.is_seller):
#             return {'error': 'Admin or seller access required'}, 403
#         return fn(*args, **kwargs)
#     return wrapper

from functools import wraps
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import User
import logging

logging.basicConfig(level=logging.DEBUG)

def user_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        logging.debug(f'User ID from JWT: {user_id}')
        user = User.query.get(user_id)
        if not user:
            logging.error('User not found')
            return {'message': 'User not found'}, 404
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        logging.debug(f'User ID from JWT: {user_id}')
        user = User.query.get(user_id)
        if not user:
            logging.error('User not found')
            return {'error': 'User not found'}, 404
        if not user.is_admin:
            logging.error('Admin access required')
            return {'error': 'Admin access required'}, 403
        logging.debug('User is admin')
        return fn(*args, **kwargs)
    return wrapper


def admin_or_seller_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        logging.debug(f'User ID from JWT: {user_id}')
        user = User.query.get(user_id)
        if not user or (not user.is_admin and not user.is_seller):
            logging.error('Admin or seller access required')
            return {'error': 'Admin or seller access required'}, 403
        return fn(*args, **kwargs)
    return wrapper
