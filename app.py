from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Sale, LoyaltyCard, Product
import os

app = Flask(__name__)
# Use environment-provided secret and database for production deploys (Render)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'saraswati_stationary_secret_key_12345')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///stationery.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/products')
def products():
    return render_template('products.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('User already exists', 'error')
        else:
            # correct usage for modern werkzeug
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()  # Commit to get ID

            # Create loyalty card
            new_card = LoyaltyCard(user_id=new_user.id)
            db.session.add(new_card)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        # Fetch all sales
        sales = Sale.query.order_by(Sale.date.desc()).all()
        return render_template('dashboard.html', sales=sales)
    else:
        # User specific data
        return render_template('dashboard.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add_sale', methods=['POST'])
@login_required
def add_sale():
    if current_user.role != 'admin':
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    amount = float(request.form.get('amount'))
    items = request.form.get('items')

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('dashboard'))

    # Record Sale
    new_sale = Sale(user_id=user.id, amount=amount, items=items)
    db.session.add(new_sale)

    # Update Loyalty Points (1 point per 10 NPR, for example)
    points_earned = int(amount / 10)
    user.loyalty_card.points += points_earned
    user.loyalty_card.update_tier()

    db.session.commit()

    flash(f'Sale recorded! {points_earned} points added to {user.username}.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role != 'admin':
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard'))

    products = Product.query.all()
    return render_template('admin_products.html', products=products)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            category=request.form['category'],
            description=request.form['description']
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('add_product.html')


@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.category = request.form['category']
        product.description = request.form['description']
        db.session.commit()

        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('edit_product.html', product=product)



@app.route('/admin/delete_product/<int:id>')
@login_required
def delete_product(id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted!', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    from sqlalchemy import func

    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 10).count()
    total_sales = db.session.query(func.sum(Sale.amount)).scalar() or 0

    return render_template(
        'admin_dashboard.html',
        total_products=total_products,
        low_stock=low_stock,
        total_sales=total_sales
    )


if __name__ == '__main__':
    if not os.path.exists('stationery.db'):
        with app.app_context():
            db.create_all()
            print("Database created.")
    app.run(debug=True)
