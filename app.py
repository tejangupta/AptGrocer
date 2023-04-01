from flask import Flask, render_template, request, jsonify
import config.mongo_coll as coll

app = Flask(__name__)


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

            return jsonify({'status': 'success'}), 200


if __name__ == '__main__':
    app.run(debug=True)
