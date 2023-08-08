from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime, timedelta
import uuid
import pymongo
from bson import ObjectId
from pymongo.errors import CollectionInvalid
import config.mongo_coll as coll
from config.auth import is_logged_in, EmailSender
from config.exception import CustomError

application = Flask(__name__)
app = application

app.secret_key = 'my_super__secret_key'

email_sender = EmailSender()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    prods = coll.products.find()

    if session.get('user_id'):
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        return render_template('index.html', products=prods, user=user)
    else:
        return render_template('index.html', products=prods)


@app.route('/product/id/<product_id>')
def product(product_id):
    try:
        prod = coll.products.find_one({'_id': product_id})

        if not prod:
            raise CustomError('Page Not Found', 404, 'Product does not exist!')

        if session.get('user_id'):
            user_id = session.get('user_id')
            user = coll.users.find_one({'_id': user_id})

            return render_template('product/product_info.html', product=prod, user=user)
        else:
            return render_template('product/product_info.html', product=prod)
    except Exception:
        raise CustomError('Page Not Found', 404, 'Page Not Found')


@app.route('/product/category/<category>')
def products_by_category(category):
    try:
        product_results = coll.products.find({'category': category.capitalize()})

        if session.get('user_id'):
            user_id = session['user_id']
            user = coll.users.find_one({'_id': user_id})

            if product_results:
                return render_template("product/product_category_results.html",
                                       mainTitle=f"{product_results[0]['category']} Products", user=user,
                                       products=product_results, category=category)
            else:
                raise CustomError('Page Not Found', 404,
                                  f'Your search did not match any products in {category} category')
        else:
            if product_results:
                return render_template("product/product_category_results.html",
                                       mainTitle=f"{product_results[0]['category']} Products",
                                       products=product_results, category=category)
            else:
                raise CustomError('Page Not Found', 404,
                                  f'Your search did not match any products in {category} category')
    except Exception:
        raise CustomError('Page Not Found', 404, 'Page Not Found')


@app.route("/product/search")
def product_search():
    keyword = request.args.get('keyword')

    if keyword:
        try:
            coll.products.create_index([('title', 'text'), ('description', 'text')])
            product_search = coll.products.find({'$text': {'$search': keyword}})

            if session.get('user_id'):
                user_id = session['user_id']
                user = coll.users.find_one({'_id': user_id})

                if product_search:
                    return render_template("product/product_search_results.html", user=user,
                                           mainTitle=f'{keyword}',
                                           products=product_search, keyword=keyword)
                else:
                    raise CustomError('Page Not Found', 404, 'Your search did not match any products.')
            else:
                if product_search:
                    return render_template("product/product_search_results.html",
                                           mainTitle=f'{keyword}',
                                           products=product_search, keyword=keyword)
                else:
                    raise CustomError('Page Not Found', 404, 'Your search did not match any products.')
        except Exception:
            raise CustomError('Page Not Found', 404, 'Page Not Found')
    else:
        return redirect('/')


@app.route('/product/search/filter', methods=['POST'])
def product_filter_search():
    if request.method == 'POST':
        search = request.json['search']
        start_range = float(request.json['startRange'])
        end_range = float(request.json['endRange'])

        try:
            filtered_products = coll.products.find({
                '$and': [
                    {'$or': [
                        {'title': {'$regex': search, '$options': 'i'}},
                        {'description': {'$regex': search, '$options': 'i'}}
                    ]},
                    {'price': {'$gte': start_range}},
                    {'price': {'$lte': end_range}}
                ]
            })

            if filtered_products:
                return jsonify({'empty': False, 'product': list(filtered_products)})
            else:
                return jsonify({'empty': True})
        except Exception as e:
            raise CustomError('Server Error', 500, e)


@app.route('/product/filter', methods=['POST'])
def product_filter():
    if request.method == 'POST':
        category = request.json['category']
        start_range = float(request.json['startRange'])
        end_range = float(request.json['endRange'])

        try:
            filtered_products = coll.products.find({
                '$and': [
                    {'category': category.capitalize()},
                    {'price': {'$gte': start_range}},
                    {'price': {'$lte': end_range}}
                ]
            })

            if filtered_products:
                return jsonify({'empty': False, 'product': list(filtered_products)})
            else:
                return jsonify({'empty': True})
        except Exception as e:
            raise CustomError('Server Error', 500, e)


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


@app.route('/user/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'GET':
        if not session.get('user_id'):
            return render_template('users/auth/user_forget_password.html')
        raise CustomError('Page Not Found', 404, 'Page Not Found')
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

    transactions_list = list(coll.orderTransaction.find({'user': user_id}).sort('_id', -1).limit(10))

    return render_template('users/gui/user_order.html', user=user, transactions=transactions_list)


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
            '_id': product_id,
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
            if item['_id'] == product_id:
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

        cart_item = coll.users.find_one({'_id': user_id, 'cart._id': prod_id}, {'cart.$': 1})['cart'][0]

        if cart_item is None:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        total_cost = quantity * cart_item['price']
        coll.users.update_one(
            {'_id': user_id, 'cart._id': prod_id},
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
        cart_item = coll.users.find_one({'_id': user_id, 'cart._id': prod_id}, {'cart.$': 1})['cart'][0]

        if cart_item is None:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        coll.users.update_one({'_id': user_id}, {'$pull': {'cart': {'_id': prod_id}}})

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


@app.route('/user/dashboard/wallet', methods=['GET', 'POST'])
@is_logged_in()
def user_wallet():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'GET':
        wallet_transactions = coll.walletTransaction.find({'user': user_id}).sort('date', pymongo.DESCENDING).limit(
            10)

        return render_template('users/gui/user_wallet.html', user=user, transactions=wallet_transactions)
    elif request.method == 'POST':
        amount = int(request.json['amount'])

        if not amount:
            raise CustomError('Bad Request', 400, 'No amount provided')

        discount_amt = taxes_amt = 0
        net_amt = amount - discount_amt + taxes_amt

        return render_template('payment/add_cash_payment_gateway.html', user=user, amount=amount, discount=discount_amt,
                               taxes=taxes_amt, net=net_amt)


@app.route('/user/update/wallet', methods=['PUT', 'POST'])
@is_logged_in()
def update_wallet():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'PUT':
        amount = request.json['amount']
        card_used = request.json['cardUsed']
        status = request.json['action']
        remark = request.json['description']

        card_info = coll.users.find_one({'_id': user_id, 'card._id': card_used}, {'card.$': 1})

        card_data = {
            'name': card_info['card'][0]['name'],
            'number': card_info['card'][0]['_id'],
            'type': card_info['card'][0]['type'],
            'expiry': card_info['card'][0]['expiry'],
            'cvv': card_info['card'][0]['cvv']
        }

        wallet_info = coll.users.update_one(
            {'_id': user_id},
            {'$inc': {'wallet': int(amount)}}
        )
        if wallet_info.modified_count == 0:
            return jsonify(data=False)

        transaction = {
            'user': user_id,
            'amount': amount,
            'cardDetails': card_data,
            'date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'status': status,
            'isCredited': True,
            'remark': remark
        }
        coll.walletTransaction.insert_one(transaction)

        user = coll.users.find_one({'_id': user_id})
        transactions_list = coll.walletTransaction.find({'user': user_id}).sort('date', pymongo.DESCENDING).limit(10)

        data = {
            'amount': user['wallet'],
            'success': True,
            'transactions': [
                {str(k): str(v) if isinstance(v, ObjectId) else v for k, v in transaction.items()}
                for transaction in transactions_list
            ]
        }

        return jsonify(data)
    elif request.method == 'POST':
        amount = request.json['amount']

        card_data = {
            'name': request.json['cardName'],
            'number': request.json['cardNumber'],
            'type': request.json['cardType'],
            'expiry': f"{request.json['cardMonth']}/{request.json['cardYear']}",
            'cvv': request.json['cardCVV']
        }
        status = "Credit"
        remark = "Added cash in wallet"

        wallet_info = coll.users.update_one(
            {'_id': user_id},
            {'$inc': {'wallet': int(amount)}}
        )
        if wallet_info.modified_count == 0:
            raise CustomError('Bad Request', 400, 'Total wallet limit exceed. Maximum $10000 are allowed.')

        transaction = {
            'user': user_id,
            'amount': amount,
            'cardDetails': card_data,
            'date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'status': status,
            'isCredited': True,
            'remark': remark
        }
        coll.walletTransaction.insert_one(transaction)

        return render_template('payment/payment_confirmation.html', user=user, redirectURL='/user/dashboard/wallet',
                               amount=amount, transactionId=str(transaction['_id']))


@app.route('/payment/checkout', methods=['GET', 'POST'])
@is_logged_in()
def product_checkout():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'GET':
        raise CustomError('Method Not Allowed', 405, 'The payment checkout requires POST request.')
    elif request.method == 'POST':
        if user:
            total_cost = 0

            for item in user['cart']:
                total_cost += item['price'] * item['qty']

            total_cost = round(total_cost, 2)
            taxes = round(total_cost * 0.07, 2)
            net_cost = round(total_cost + taxes, 2)

            w_flag = True
            if user.get('wallet', 0) < net_cost:
                w_flag = False

            return render_template('payment/payment_gateway.html', user=user, total=total_cost, tax=taxes, net=net_cost,
                                   isWallet=w_flag)
        else:
            raise CustomError('Page Not Found', 404, 'Page Not Found')


@app.route('/payment/gateway/saved', methods=['POST'])
@is_logged_in()
def saved_card_payment():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'POST':
        card_number = request.form['savedCard']
        amount = request.form['amount']
        card = None

        for c in user['card']:
            if c['_id'] == card_number:
                card = c
                break

        if not card:
            raise CustomError('Bad Request', 400, 'Invalid Card')

        cart_items = []
        for item in user['cart']:
            cart_items.append({
                '_id': item['_id'],
                'title': item['title'],
                'qty': item['qty'],
                'price': item['price'],
                'total': item['total']
            })

        if not cart_items:
            raise CustomError('Bad Request', 400, 'No Items in cart')

        try:
            # Log transaction
            trans_id = coll.orderTransaction.insert_one({
                'user': user['_id'],
                'amount': amount,
                'card': card,
                'items': cart_items,
                'payMode': 'Saved Card',
                'date': datetime.utcnow()
            }).inserted_id

            # empty cart
            coll.users.update_one({'_id': user['_id']}, {'$set': {'cart': [], 'cartLen': 0}})

            return render_template('payment/payment_confirmation.html', user=user, redirectURL='/user/dashboard/cart',
                                   amount=amount, orderId=trans_id)
        except Exception as e:
            raise CustomError('Server Error', 500, e)


@app.route('/payment/gateway/new', methods=['POST'])
@is_logged_in()
def new_card_payment():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'POST':
        # Validate new card information
        user_updates = request.form
        amount = request.form['amount']

        if not user_updates or not user_updates.get('cardName') or not user_updates.get('cardNumber') \
                or not user_updates.get('cardType') or not user_updates.get('expMonth') or not user_updates.get(
            'expYear') \
                or not user_updates.get('cardCVV'):
            raise CustomError('Forbidden', 403, 'Invalid payment information')

        card_data = {
            'number': user_updates['cardNumber'],
            'name': user_updates['cardName'],
            'type': user_updates['cardType'],
            'expiry': user_updates['expMonth'] + '/' + user_updates['expYear'],
            'cvv': user_updates['cardCVV']
        }

        cart_items = []
        for item in user['cart']:
            cart_items.append({
                '_id': item['_id'],
                'title': item['title'],
                'qty': item['qty'],
                'price': item['price'],
                'total': item['total']
            })

        if not cart_items:
            raise CustomError('Bad Request', 400, 'No Items in cart')

        try:
            # Log transaction
            trans_id = coll.orderTransaction.insert_one({
                'user': user['_id'],
                'amount': amount,
                'card': card_data,
                'items': cart_items,
                'payMode': 'New Card',
                'date': datetime.utcnow()
            }).inserted_id

            # empty cart
            coll.users.update_one({'_id': user['_id']}, {'$set': {'cart': [], 'cartLen': 0}})

            return render_template('payment/payment_confirmation.html', user=user, redirectURL='/user/dashboard/cart',
                                   amount=amount, orderId=trans_id)
        except Exception as e:
            raise CustomError('Server Error', 500, e)


@app.route('/payment/gateway/wallet', methods=['POST'])
@is_logged_in()
def wallet_payment():
    user_id = session.get('user_id')
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'POST':
        amount = float(request.form['amount'])

        cart_items = []
        for item in user['cart']:
            cart_items.append({
                '_id': item['_id'],
                'title': item['title'],
                'qty': item['qty'],
                'price': item['price'],
                'total': item['total']
            })

        if not cart_items:
            raise CustomError('Bad Request', 400, 'No Items in cart')

        try:
            # Log transaction
            trans_id = coll.orderTransaction.insert_one({
                'user': user['_id'],
                'amount': str(amount),
                'card': {},
                'items': cart_items,
                'payMode': 'Wallet',
                'date': datetime.utcnow()
            }).inserted_id

            # empty cart
            coll.users.update_one({'_id': user['_id']}, {'$set': {'cart': [], 'cartLen': 0}})

            # Deduct amount from wallet
            wallet = coll.users.find_one({'_id': user['_id']}, {'_id': 0, 'wallet': 1})['wallet']

            if wallet < amount:
                raise CustomError('Payment Failed', 400, 'Insufficient Balance in Wallet')
            else:
                new_wallet_balance = round((wallet - amount), 2)

            coll.walletTransaction.insert_one({
                'user': user['_id'],
                'amount': str(amount),
                'cardDetails': {},
                'date': datetime.utcnow(),
                'status': 'Debit',
                'isCredited': False,
                'remark': 'Purchase Order#' + str(trans_id)
            })

            coll.users.update_one({'_id': user['_id']}, {'$set': {'wallet': new_wallet_balance}})

            # Render success page
            return render_template('payment/payment_confirmation.html', user=user,
                                   redirectURL='/user/dashboard/cart', amount=amount, orderId=trans_id)
        except CustomError as e:
            raise CustomError('Server Error', 500, e)


@app.route('/support/contact-us', methods=['POST'])
def contact_us():
    if request.method == 'POST':
        sender_info = {
            'name': request.json['name'],
            'email': request.json['email'],
            'mobile': request.json['mobile'],
            'description': request.json['description']
        }

        contact = {
            'name': sender_info['name'],
            'email': sender_info['email'],
            'mobile': sender_info['mobile'],
            'description': sender_info['description'],
            'contactedDate': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }

        # inserting the document into MongoDB collection
        try:
            coll.contacts.insert_one(contact)
            return jsonify({'success': 'true'})
        except CollectionInvalid:
            raise CustomError('Server Error', 500, 'collectionError')


@app.route('/support/subscription/status')
@is_logged_in()
def subscription_status():
    try:
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        # search for subscription record by user ID
        subscription = coll.subscriptions.find_one({'_id': user_id})

        # if subscription record exists, render template with status, otherwise render with status=False
        if subscription:
            return render_template('support/subscription.html', user=user, status=subscription['activeStatus'])
        else:
            return render_template('support/subscription.html', user=user, status=False)
    except Exception:
        raise CustomError('Page Not Found', 404, 'Page Not Found')


@app.route('/support/subscription/status/<email>')
def subscription_status_anonymous(email):
    try:
        user_id = session.get('user_id')
        user = coll.users.find_one({'_id': user_id})

        # If anonymous user is logged in as themselves, redirect to their own subscription status
        if user and email == user_id:
            return redirect('/support/subscription/status')

        # Search for subscription record by email
        subscription = coll.subscriptions.find_one({'_id': email})

        # If subscription record exists, render template with status, otherwise render with status=False
        if subscription:
            return render_template('support/subscription.html', anonymous=True)
        else:
            return render_template('support/subscription.html', anonymous=False)
    except Exception:
        raise CustomError('Page Not Found', 404, 'Page Not Found')


@app.route('/support/subscription/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.json['email']

        try:
            subscription = coll.subscriptions.find_one({'_id': email})

            if subscription is None:
                coll.subscriptions.insert_one({'_id': email, 'activeStatus': True})
            else:
                coll.subscriptions.update_one({'_id': email}, {'$set': {'activeStatus': True}})

            return jsonify({'email': email})
        except CollectionInvalid:
            raise CustomError('Server Error', 500, 'collectionError')


@app.route('/support/subscription/unsubscribe', methods=['POST'])
def unsubscribe():
    if request.method == 'POST':
        email = session.get('user_id')

        # Updating a record
        try:
            coll.subscriptions.update_one({'_id': email}, {'$set': {'activeStatus': False}})

            return redirect(url_for('subscription_status'))
        except CollectionInvalid:
            raise CustomError('Server Error', 500, 'collectionError')


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
    app.run(host='0.0.0.0', port=8000)
