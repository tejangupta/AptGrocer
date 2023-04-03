from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import secrets
import string
import uuid
from bson import ObjectId
import config.mongo_coll as coll
from config.auth import is_logged_in, send_verification_email

app = Flask(__name__)
app.secret_key = 'my_super__secret_key'


@app.route('/')
def index():
    prods = coll.products.find()

    if session.get('user_id'):
        user_id = ObjectId(session.get('user_id'))
        user = coll.users.find_one({'_id': user_id})

        return render_template('index.html', products=prods, user=user)
    else:
        return render_template('index.html', products=prods)


@app.route('/product/id/<id>')
def product(id):
    prod = coll.products.find_one({'_id': id})

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
            send_verification_email(email, verification_token)

            return jsonify({'success': 'true'})


@app.route('/verify_email/<verification_token>', methods=['GET'])
def verify_email(verification_token):
    user = coll.users.find_one({'verification_token': verification_token})
    if user is not None:
        if not user.get('verified', False):
            user['verified'] = True
            coll.users.replace_one({'_id': user['_id']}, user)

            return render_template('alerts/success.html',
                                   success='Email verified successfully',
                                   code=200,
                                   message='Email verified successfully!',
                                   url=request.url)
        else:
            return render_template('alerts/error.html',
                                   error='Email already verified',
                                   url=request.url,
                                   code='400 Bad Request',
                                   message='Email already verified!')
    else:
        return render_template('alerts/error.html',
                               error='Invalid verification token',
                               url=request.url,
                               code='400 Bad Request',
                               message='Invalid verification token!')


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

        return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('alerts/error.html',
                               error='Invalid Logout Request - Must Use POST',
                               url=request.url,
                               code='405 Method Not Allowed',
                               message='''The logout endpoint requires a POST request. Please use a POST request to log 
                                       out of the system.''',
                               user=user)


@app.route('/user/dashboard')
@is_logged_in()
def dashboard():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    return render_template('users/gui/user_dashboard.html', user=user)


@app.route('/user/dashboard/cart')
# @is_logged_in()
def cart():
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


if __name__ == '__main__':
    app.run(debug=True)
