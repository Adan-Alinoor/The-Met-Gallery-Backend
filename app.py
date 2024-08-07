from flask import Flask,request
from flask_restful import Api,Resource
from flask_migrate import Migrate
from model import db,User
import bcrypt

# from flask import Flask, request, jsonify
# from flask_restful import Api, Resource, reqparse
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
# from flask_migrate import Migrate
# from model import db, User  
# import bcrypt
# from auth import admin_required
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  

db.init_app(app)
api = Api(app)
migrate = Migrate(app, db)

class Signup(Resource):
    def post(self):
        args = request.get_json()
        if not all(k in args for k in ('username', 'email', 'password', 'role')):
            return {'message': 'Username, email, password, and role are required'}, 400
        
        hashed_password = bcrypt.hashpw(args['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=args['username'], email=args['email'], password=hashed_password, role=args['role'])
        db.session.add(new_user)
        db.session.commit()

        return {'message': f"{args['role'].capitalize()} created successfully"}, 201

if __name__ == '__main__':
    app.run(debug=True)