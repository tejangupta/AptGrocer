from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import secrets
import string
import uuid
from bson import ObjectId
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
        user_id = ObjectId(session.get('user_id'))
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
        user_id = ObjectId(session.get('user_id'))
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
        existing_user = coll.users.find_one({'email': email})
        if existing_user is not None:
            return '', 400
        else:
            # Generate verification token for new user
            verification_token = str(uuid.uuid4())

            # Create new user with unverified status
            new_user = {
                'name': name,
                'email': email,
                'mobile': mobile,
                'password': password,
                'verified': False,
                'verification_token': verification_token
            }
            coll.users.insert_one(new_user)

            # Send verification email to the user's email address
            email_sender.send_verification_email(email, verification_token)

            return jsonify({'success': 'true'})


@app.route('/verify_email/<verification_token>', methods=['GET'])
def verify_email(verification_token):
    user = coll.users.find_one({'verification_token': verification_token})
    if user is not None:
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

        user = coll.users.find_one({'email': email})
        if user is None:
            return jsonify({'message': 'This email id is not registered'}), 400
        elif user['password'] != password:
            return jsonify({'message': 'Incorrect password'}), 400
        elif not user['verified']:
            return jsonify({'message': 'You have not verified your email'}), 400
        else:
            session['user_id'] = str(user['_id'])
            session.modified = True

            return jsonify({'success': 'true', 'url': '/user/dashboard'})


@app.route('/user/logout', methods=['GET', 'POST'])
@is_logged_in()
def logout():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'POST':
        session.pop('user_id', None)

        return redirect('/')
    elif request.method == 'GET':
        raise CustomError('Method Not Allowed', 405, 'The logout endpoint requires POST request.')


@app.route('/user/dashboard')
@is_logged_in()
def dashboard():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    return render_template('users/gui/user_dashboard.html', user=user)


@app.route('/user/update/cart/<product_id>/<loc>', methods=['POST'])
@is_logged_in()
def update_cart(product_id, loc):
    user_id = ObjectId(session.get('user_id'))
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
            'image': product['images'],
        }

        cart = coll.usersCart.find_one({'_id': user_id})

        if cart is None:
            cart = {
                '_id': user_id,
                'items': [cart_item],
                'cart_length': 1
            }
            coll.usersCart.insert_one(cart)
        else:
            product_in_cart = False
            for item in cart['items']:
                if item['product_id'] == product_id:
                    product_in_cart = True
                    break
            if not product_in_cart:
                coll.usersCart.update_one(
                    {'_id': user_id},
                    {
                        '$push': {'items': cart_item},
                        '$inc': {'cart_length': 1}
                    }
                )
            cart = coll.usersCart.find_one({'_id': user_id})

        if loc == 'home':
            return redirect(url_for('update_cart_quantity'))
        elif loc == 'product-view':
            return render_template('product/product_added_cart.html', cart=cart, user=user)


@app.route('/user/update/cart', methods=['PUT', 'DELETE'])
@is_logged_in()
def update_cart_quantity():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    if request.method == 'PUT':
        quantity = int(request.json['qty'])
        prod_id = request.json['id']

        if quantity < 1 or quantity > 5:
            return jsonify({'success': 'false'})

        cart_item = coll.usersCart.find_one({'product_id': prod_id})

        if not cart_item:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        coll.usersCart.update_one({'_id': user_id, 'product_id': prod_id}, {'$set': {'items.$.qty': quantity}})

        # Update cart_length to be the sum of qty for all items in cart
        cart_length = sum(item['qty'] for item in cart['items'])
        coll.usersCart.update_one({'_id': user_id}, {'$set': {'cart_length': cart_length}})

        return jsonify({'success': 'true'})
    elif request.method == 'DELETE':
        prod_id = request.json['id']
        cart_item = coll.usersCart.find_one({'product_id': prod_id})

        if not cart_item:
            raise CustomError('Bad Request', 400, 'Invalid product id')

        coll.usersCart.update_one({'_id': user_id}, {'$pull': {'items': {'product_id': prod_id}}})

        # Update cart_length to be the sum of qty for all items in cart
        cart_length = sum(item['qty'] for item in cart['items'])
        coll.usersCart.update_one({'_id': user_id}, {'$set': {'cart_length': cart_length}})

        return jsonify({'success': 'true', 'cartSize': cart_length})


@app.route('/user/dashboard/cart')
@is_logged_in()
def cart():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    total_cost = taxes = net_cost = 0

    for item in user['cart']:
        pass


@app.route('/user/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'GET':
        return render_template('users/auth/user_forget_password.html')
    elif request.method == 'POST':
        email = request.json['email'].lower()

        # Searching for an existing email
        if coll.users.find_one({'email': email}) is None:
            return '', 404
        else:
            new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            coll.credentials.update_one({'email': email}, {'$set': {'password': new_password}})

            return jsonify({'success': 'true', 'email': email, 'password': new_password})


@app.errorhandler(CustomError)
def error_handler(e):
    if session.get('user_id'):
        user_id = ObjectId(session.get('user_id'))
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
