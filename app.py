from flask import Flask, render_template
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


if __name__ == '__main__':
    app.run(debug=True)
