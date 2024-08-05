'''
class MpesaPaymentResource(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        order_id = data.get('order_id')
        phone_number = data.get('phone_number')
        amount = data.get('amount')

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        order = Order.query.get(order_id)
        if not order:
            return {'error': 'Order not found'}, 404

        # Create a new Payment record
        payment = Payment(user_id=user.id, order_id=order.id, amount=amount, phone_number=phone_number)
        db.session.add(payment)
        db.session.commit()

        # Call M-Pesa API to initiate payment
        access_token = get_mpesa_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        password, timestamp = generate_password(SHORTCODE, LIPA_NA_MPESA_ONLINE_PASSKEY)
        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://ab30-102-214-74-3.ngrok-free.app/callback",
            "AccountReference": f"Order{order.id}",
            "TransactionDesc": "Payment for order"
        }
        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            headers=headers,
            json=payload
        )

        response_data = response.json()
        if response_data.get('ResponseCode') == '0':
            payment.transaction_id = response_data['CheckoutRequestID']
            payment.status = 'initiated'
            db.session.commit()
            return {'message': 'Payment initiated successfully'}, 201
        else:
            return {'error': 'Failed to initiate payment'}, 400

'''
'''
class CheckoutResource(Resource):
    def post(self):
        data = request.get_json()

        user_id = data.get('user_id')
        if not user_id:
            return {'error': 'User ID is required'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        cart = Cart.query.filter_by(user_id=user.id).first()
        if not cart or not cart.items:
            return {'error': 'Cart is empty'}, 400

        order = Order(user_id=user.id)
        db.session.add(order)
        db.session.commit()

        total_amount = 0
        for item in cart.items:
            total_amount += item.price * item.quantity

        payment_data = {
            'user_id': user.id,
            'order_id': order.id,
            'phone_number': data.get('phone_number'),
            'amount': total_amount
        }

        # Initiate payment through M-Pesa
        mpesa_resource = MpesaPaymentResource()
        payment_response = mpesa_resource.post(payment_data)

        if payment_response[1] != 201:
            return {'error': 'Failed to initiate payment'}, 400

        # Clear the cart
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

        return {
            'message': 'Order created and payment initiated successfully',
            'order_id': order.id,
            'payment_response': payment_response
        }, 201
i didnt user the mpesa paymet route
api.add_resource(MpesaPaymentResource, '/mpesa_payment'


'''