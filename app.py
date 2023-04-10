from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime, timedelta
import uuid
import config.mongo_coll as coll
from config.auth import is_logged_in, EmailSender
from config.exception import CustomError

app = Flask(__name__)
app.secret_key = 'my_super__secret_key'

email_sender = EmailSender()


@app.route('/')
def index():
    prods = coll.products.find()

    if session.get('user_id'):
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        return render_template('index.html', products=prods, user=user)
    else:
        return render_template('index.html', products=prods)


@app.route('/product/id/<product_id>')
def product(product_id):
    prod = coll.products.find_one({'_id': product_id})

    if not prod:
        raise CustomError('Page Not Found', 404, 'Product does not exist!')

    if session.get('user_id'):
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        return render_template('product/product_info.html', product=prod, user=user)
    else:
        return render_template('product/product_info.html', product=prod)


# Route to render the create new user form and create new user into database
@app.route('/user/new', methods=['GET', 'POST'])
def create_new_user():
    if request.method == 'GET':
        return render_template('users/auth/create_new_account.html')
    elif request.method == 'POST':
        name = request.json['name']
        email = request.json['email'].lower()
        mobile = request.json['mobile']
        password = request.json['password']

        # Searching for an existing user
        existing_user = coll.users.find_one({'_id': email})
        if existing_user is not None:
            return '', 400
        else:
            # Generate verification token for new user
            verification_token = str(uuid.uuid4())

            # Create new user with unverified status
            new_user = {
                '_id': email,
                'name': name,
                'alias': name.split()[0],
                'mobile': mobile,
                'verified': False,
                'verification_token': verification_token
            }
            coll.users.insert_one(new_user)

            # Create new credential
            new_credential = {
                '_id': email,
                'password': password
            }
            coll.credentials.insert_one(new_credential)

            # Send verification email to the user's email address
            email_sender.send_verification_email(email, verification_token)

            return jsonify({'success': 'true'})


@app.route('/verify_email/<verification_token>', methods=['GET'])
def verify_email(verification_token):
    user = coll.users.find_one({'verification_token': verification_token})
    if user:
        if not user.get('verified', False):
            user['verified'] = True
            coll.users.replace_one({'_id': user['_id']}, user)

            return render_template('alerts/success.html',
                                   success='OK',
                                   code=200,
                                   message='Email verified successfully!',
                                   url=request.url)
        else:
            raise CustomError('Bad Request', 400, 'Email already verified!')
    else:
        raise CustomError('Bad Requesst', 400, 'Invalid verification token!')


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('users/auth/user_login_account.html')
    elif request.method == 'POST':
        email = request.json['email'].lower()
        password = request.json['password']

        user = coll.credentials.find_one({'_id': email})
        if user is None:
            return jsonify({'message': 'This email id is not registered'}), 400
        elif user['password'] != password:
            return jsonify({'message': 'Incorrect password'}), 400
        elif not coll.users.find_one({'_id': email})['verified']:
            return jsonify({'message': 'You have not verified your email'}), 400
        else:
            session['user_id'] = user['_id']
            session.modified = True

            return jsonify({'success': 'true', 'url': '/user/dashboard'})


@app.route('/user/logout', methods=['GET', 'POST'])
@is_logged_in()
def logout():
    if request.method == 'POST':
        session.pop('user_id', None)

        return redirect('/')
    elif request.method == 'GET':
        raise CustomError('Method Not Allowed', 405, 'The logout endpoint requires POST request.')


@app.route('/user/dashboard')
@is_logged_in()
def dashboard():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    return render_template('users/gui/user_dashboard.html', user=user)


@app.route('/user/update/cart/<product_id>/<loc>', methods=['POST'])
@is_logged_in()
def update_cart(product_id, loc):
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'POST':
        if not product_id:
            raise CustomError('Server Error', 500, 'No product selected!')

        product = coll.products.find_one({'_id': product_id})

        if not product:
            raise CustomError('Page Not Found', 404, 'Product does not exist!')

        cart_item = {
            'product_id': product_id,
            'title': product['title'],
            'description': product['description'],
            'size': product['size'],
            'price': product['price'],
            'images': product['images'],
            'qty': 1,
            'total': product['price']
        }

        # Check if the item is already in cart
        product_in_cart = False
        for item in user.get('cart', []):
            if item['product_id'] == product_id:
                product_in_cart = True
                break

        # If the item is not in cart, add it and increment cartLen
        if not product_in_cart:
            user.setdefault('cart', []).append(cart_item)
            user['cartLen'] = user.get('cartLen', 0) + 1

        coll.users.update_one({'_id': user_id}, {'$set': user}, upsert=False)

        if loc == 'home':
            return redirect(url_for('update_cart_quantity'))
        elif loc == 'product-view':
            return render_template('product/product_added_cart.html', user=user)


@app.route('/user/update/cart', methods=['PUT', 'DELETE'])
@is_logged_in()
def update_cart_quantity():
    user_id = session.get('user_id')

    if request.method == 'PUT':
        quantity = int(request.json['qty'])
        prod_id = request.json['id']

        if quantity < 1 or quantity > 5:
            return jsonify(success=False)

        cart_item = coll.users.find_one({'_id': user_id, 'cart.product_id': prod_id}, {'cart.$': 1})['cart'][0]

        if cart_item is None:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        total_cost = quantity * cart_item['price']
        coll.users.update_one(
            {'_id': user_id, 'cart.product_id': prod_id},
            {'$set': {'cart.$.qty': quantity, 'cart.$.total': total_cost}},
            upsert=True
        )

        user = coll.users.find_one({'_id': user_id})

        # Update cart_length to be the sum of qty for all cart objects
        cart_length = sum(item['qty'] for item in user['cart'])
        coll.users.update_one({'_id': user_id}, {'$set': {'cartLen': cart_length}})

        return jsonify(success=True)
    elif request.method == 'DELETE':
        prod_id = request.json['id']
        cart_item = coll.users.find_one({'_id': user_id, 'cart.product_id': prod_id}, {'cart.$': 1})['cart'][0]

        if cart_item is None:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        coll.users.update_one({'_id': user_id}, {'$pull': {'cart': {'product_id': prod_id}}})

        user = coll.users.find_one({'_id': user_id})

        # Update cart_length to be the sum of qty for all items in cart
        cart_length = sum(item['qty'] for item in user['cart'])
        coll.users.update_one({'_id': user_id}, {'$set': {'cartLen': cart_length}})

        return jsonify({'success': 'true', 'cartSize': cart_length})


@app.route('/user/dashboard/cart')
@is_logged_in()
def cart():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})
    user_cart = user.get('cart', [])

    total_cost, taxes, net_cost = 0, 0, 0

    for item in user_cart:
        total_cost += item['total']

    total_cost = round(total_cost * 100) / 100
    taxes = round(total_cost * 0.07 * 100) / 100
    net_cost = round((total_cost + taxes) * 100) / 100

    return render_template('users/gui/user_cart.html', user=user, total=total_cost, tax=taxes, net=net_cost)


@app.route('/user/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'GET':
        return render_template('users/auth/user_forget_password.html')
    elif request.method == 'POST':
        email = request.json['email'].lower()

        # Searching for an existing email
        if coll.users.find_one({'_id': email}) is None:
            return '', 404
        else:
            verification_token = str(uuid.uuid4())
            expiry_time = datetime.utcnow() + timedelta(minutes=10)

            # Update the credentials collection with the verification token and expiry time
            coll.credentials.update_one({'_id': email}, {
                '$set': {'verification_token': verification_token, 'expiry_time': expiry_time}})

            # Send email to update password
            email_sender.update_password_email(email, verification_token)

            return jsonify({'success': 'true'})


@app.route('/update_password/<verification_token>', methods=['GET', 'POST'])
def update_password(verification_token):
    user = coll.credentials.find_one({'verification_token': verification_token})
    if user:
        expiry_time = user.get('expiry_time')
        if expiry_time is not None and expiry_time < datetime.utcnow():
            # Token has expired
            raise CustomError('Bad Request', 400, 'Verification token has expired!')
        else:
            # Token is valid, allow user to update password
            if request.method == 'GET':
                return render_template('users/auth/enter_new_password.html')
            elif request.method == 'POST':
                new_password = request.json['password']

                coll.credentials.update_one({'_id': user['_id']},
                                            {'$set': {'password': new_password}, '$unset': {'verification_token': ""}})

                return jsonify({'success': 'true'})
    else:
        raise CustomError('Bad Request', 400, 'Invalid verification token!')


@app.route('/user/dashboard/account', methods=['GET', 'POST'])
@is_logged_in()
def update_user_info():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'GET':
        return render_template('users/gui/user_account.html', user=user)
    elif request.method == 'POST':
        user_updates = request.json

        if 'name' in user_updates and 'mobile' in user_updates:
            name = user_updates.get('name')
            mobile = user_updates.get('mobile')

            coll.users.update_one({'_id': user_id}, {'$set': dict(name=name, alias=name.split()[0], mobile=mobile)})

            return jsonify(success=True)
        elif 'password' in user_updates and len(request.json['password']) > 0:
            password = user_updates.get('password')
            current_password = coll.credentials.find_one({'_id': user_id})['password']
            if password != current_password:
                coll.credentials.update_one({'_id': user_id}, {'$set': {'password': password}})
            else:
                return jsonify({'success': 'false', 'error': 'New password should be different from previous password'})

            return jsonify(success=True)


@app.route('/user/dashboard/payments', methods=['GET', 'POST', 'DELETE'])
@is_logged_in()
def update_user_card():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'GET':
        return render_template('users/gui/user_card.html', user=user)
    elif request.method == 'POST':
        user_updates = request.json
        card_number = user_updates.get('number')

        # Check if card already exists in user's card list
        if any(card.get('_id') == card_number for card in user.get('card', [])):
            return '', 400

        # Add new card to user's card list
        new_card = {
            '_id': card_number,
            'name': user_updates.get('username'),
            'type': user_updates.get('type'),
            'expiry': user_updates.get('exp'),
            'cvv': user_updates.get('cvv')
        }
        coll.users.update_one({'_id': user_id}, {'$push': {'card': new_card}})

        return jsonify({'success': 'true'})
    elif request.method == 'DELETE':
        user_updates = request.json
        card_number = user_updates.get('cardNumber')
        coll.users.update_one({'_id': user_id}, {'$pull': {'card': {'_id': str(card_number)}}})

        return jsonify({'success': True})


@app.route('/user/dashboard/order-history')
@is_logged_in()
def order_hist():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    transactions = coll.orderTransaction.find({'user': user_id})
    transactions_list = []

    for transaction in transactions:
        transactions_list.append(transaction)

    transactions_list.reverse()
    transactions_list = transactions_list[:10]

    return render_template('users/gui/user_order.html', user=user, transactions=transactions_list)


@app.errorhandler(CustomError)
def error_handler(e):
    if session.get('user_id'):
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        return render_template('alerts/error.html',
                               error=e.error,
                               url=request.url,
                               code=e.code,
                               message=e.message,
                               user=user)
    else:
        return render_template('alerts/error.html',
                               error=e.error,
                               url=request.url,
                               code=e.code,
                               message=e.message)


if __name__ == '__main__':
    app.run(debug=True)
