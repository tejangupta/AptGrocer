from flask import Flask, render_template, request, jsonify, session
import secrets
import string
from bson import ObjectId
import config.mongo_coll as coll
from config.auth import is_logged_in

app = Flask(__name__)
app.secret_key = 'my_super__secret_key'


@app.route('/')
def index():
    prods = coll.products.find()
    return render_template('index.html', products=prods)


@app.route('/product/id/<id>')
def product(id):
    prod = coll.products.find_one({'_id': id})
    return render_template('product/product_info.html', product=prod)


# Route to render the create new user form and create new user into database
@app.route('/user/new', methods=['GET', 'POST'])
@is_logged_in('/user/new')
def create_new_user():
    if request.method == 'GET':
        return render_template('users/auth/create_new_account.html')
    elif request.method == 'POST':
        name = request.json['name']
        email = request.json['email'].lower()
        mobile = request.json['mobile']
        password = request.json['password']

        # Searching for an existing user
        if coll.users.find_one({'email': email}) is not None:
            return '', 400
        else:
            new_user = {
                'name': name,
                'email': email,
                'mobile': mobile
            }
            coll.users.insert_one(new_user)

            new_credential = {
                'email': email,
                'password': password
            }
            coll.credentials.insert_one(new_credential)

            return jsonify({'success': 'true'})


@app.route('/user/login', methods=['GET', 'POST'])
@is_logged_in()
def user_login():
    if request.method == 'GET':
        return render_template('users/auth/user_login_account.html')
    elif request.method == 'POST':
        email = request.json['email'].lower()
        password = request.json['password']

        user = coll.users.find_one({'email': email})
        if user is None:
            return '', 404

        if coll.credentials.find_one({'email': email})['password'] != password:
            return '', 400
        else:
            session['user_id'] = str(user['_id'])
            session.modified = True

            return jsonify({'success': 'true', 'url': '/user/dashboard'})


@app.route('/user/dashboard')
@is_logged_in('/user/dashboard')
def dashboard():
    user_id = ObjectId(session.get('user_id'))
    user = coll.users.find_one({'_id': user_id})

    return render_template('users/gui/user_dashboard.html', user=user)


@app.route('/user/forget-password', methods=['GET', 'POST'])
@is_logged_in('/user/forget-password')
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
