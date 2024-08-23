from flask import request, jsonify
from flask_restful import Resource
from models import db, Payment, Order, Artwork, Booking, Event

class PaymentResource(Resource):
    def get(self):
        try:
            payments = Payment.query.all()
            serialized_payments = [payment.serialize() for payment in payments]
            return jsonify(serialized_payments)
        except Exception as e:
            return {'error': str(e)}, 500

class OrderDetailsResource(Resource):
    def get(self, order_id):
        try:
            # Fetch the order
            order = Order.query.get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            # Fetch related artworks
            items = order.items
            artworks = []
            for item in items:
                artwork = Artwork.query.get(item.artwork_id)
                if artwork:
                    artworks.append(artwork.to_dict())

            # Create a response dictionary
            order_details = {
                'order': order.to_dict(),
                'items': artworks,
            }

            return order_details, 200
        except Exception as e:
            return {"error": str(e)}, 500


class BookingDetailsResource(Resource):
    def get(self, booking_id):
        try:
            # Fetch the booking
            booking = Booking.query.get(booking_id)
            if not booking:
                return {"error": "Booking not found"}, 404

            # Fetch the related event
            event = Event.query.get(booking.event_id)
            if not event:
                return {"error": "Event not found"}, 404

            # Create a response dictionary
            booking_details = {
                'booking': booking.to_dict(),
                'event': event.to_dict(),
            }

            return booking_details, 200
        except Exception as e:
            return {"error": str(e)}, 500
