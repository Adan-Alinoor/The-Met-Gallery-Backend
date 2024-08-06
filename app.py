from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy
from models import Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['JWT_SECRET_KEY'] = 'my_jwt_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    data = request.json
    recipient_id = data.get('recipient_id')
    message_text = data.get('message')
    sender_id = get_jwt_identity()

    if not recipient_id or not message_text:
        return jsonify({"error": "Invalid data"}), 400

    new_message = Message(sender=sender_id, recipient=recipient_id, message=message_text)
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('new_message', {
        'sender': sender_id,
        'recipient': recipient_id,
        'message': message_text,
        'timestamp': new_message.timestamp.isoformat()
    }, broadcast=True)

    return jsonify({"message": "Message sent"}), 201

@app.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    user_id = get_jwt_identity()
    messages = Message.query.filter((Message.sender == user_id) | (Message.recipient == user_id)).all()
    
    return jsonify([{
        'id': msg.id,
        'sender': msg.sender,
        'recipient': msg.recipient,
        'message': msg.message,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages])
    

if __name__ == '__main__':
    socketio.run(app, debug=True)
