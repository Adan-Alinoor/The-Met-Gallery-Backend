from flask import Flask
from flask_restful import Api
from flask_migrate import Migrate
from model import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  

db.init_app(app)
api = Api(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)