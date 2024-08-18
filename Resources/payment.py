from flask import request, jsonify
from flask_restful import Resource
from models import db, Payment

class PaymentResource(Resource):
    def get(self):
        try:
            payments = Payment.query.all()
            serialized_payments = [payment.serialize() for payment in payments]
            return jsonify(serialized_payments)
        except Exception as e:
            return {'error': str(e)}, 500
