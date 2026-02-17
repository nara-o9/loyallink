from flask import Flask, render_template, redirect, url_for, request, flash, abort, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Sale, LoyaltyCard, Product, PointsTransaction, Reward, Order, OrderItem
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
import requests

app = Flask(__name__)
# Use environment-provided secret and database for production deploys (Render)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'saraswati_stationary_secret_key_12345')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///stationery.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khalti Payment Configuration
app.config['KHALTI_PUBLIC_KEY'] = os.environ.get('KHALTI_PUBLIC_KEY', 'test_public_key_xxx')
app.config['KHALTI_SECRET_KEY'] = os.environ.get('KHALTI_SECRET_KEY', 'test_secret_key_xxx')

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============ FILE HANDLING FUNCTIONS ============
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_product_image(file, old_filename=None):
    """Save uploaded product image and return filename"""
    if not file or file.filename == '':
        return old_filename  # Return existing filename if no new file
    
    if not allowed_file(file.filename):
        raise ValueError('Only jpg, jpeg, png, and webp files are allowed')
    
    # Delete old image if replacing
    if old_filename and old_filename not in ['placeholder.png', 'placeholder.svg']:
        old_path = os.path.join(UPLOAD_FOLDER, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass  # Silently ignore if deletion fails
    
    # Generate filename with timestamp to prevent collisions
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + secure_filename(file.filename)
    
    # Save file
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    return filename


def delete_product_image(filename):
    """Delete product image file"""
    if filename and filename != 'placeholder.svg' and filename != 'placeholder.png':
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass  # Silently ignore if deletion fails


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)


@app.route('/product/<int:id>')
def product_detail(id):
    """Display product detail page"""
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to shopping cart (session-based)"""
    product = Product.query.get_or_404(product_id)
    
    # Check stock
    if product.stock <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Product out of stock'}), 400
        flash('Product is out of stock', 'error')
        return redirect(url_for('product_detail', id=product_id))
    
    # Initialize cart in session
    if 'cart' not in session:
        session['cart'] = {}
    
    quantity = int(request.form.get('quantity', 1))
    product_id_str = str(product_id)
    
    # Add/update cart item
    if product_id_str in session['cart']:
        session['cart'][product_id_str]['quantity'] += quantity
    else:
        session['cart'][product_id_str] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image_url': product.get_image_url()
        }
    
    session.modified = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': sum(item['quantity'] for item in session['cart'].values())})
    
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    """Display shopping cart"""
    cart_items = []
    subtotal = 0
    
    if 'cart' in session:
        for product_id, item in session['cart'].items():
            item_subtotal = item['price'] * item['quantity']
            subtotal += item_subtotal
            cart_items.append({
                'product_id': product_id,
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'subtotal': item_subtotal,
                'image_url': item['image_url']
            })
    
    # Delivery charges
    delivery_charges = {
        'standard': 0,
        'express': 150,
        'pickup': 0
    }
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         subtotal=subtotal,
                         delivery_charges=delivery_charges)


@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove product from cart"""
    if 'cart' in session:
        product_id_str = str(product_id)
        if product_id_str in session['cart']:
            del session['cart'][product_id_str]
            session.modified = True
            flash('Item removed from cart', 'success')
    
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page"""
    if not session.get('cart'):
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    # Pre-fill form for logged in users
    user_data = {
        'full_name': current_user.username,
        'email': current_user.email,
    }
    return render_template('checkout.html', user_data=user_data)


@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Create order from cart"""
    
    if not session.get('cart'):
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    try:
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        delivery_option = request.form.get('delivery_option', 'standard')
        payment_method = request.form.get('payment_method', 'cod')
        
        # Validate
        if not all([full_name, email, phone, address, city, postal_code]):
            flash('All fields are required', 'error')
            return redirect(url_for('checkout'))
        
        # Calculate totals
        subtotal = 0
        cart_for_db = []
        
        for product_id, item in session['cart'].items():
            product = Product.query.get(int(product_id))
            if not product or product.stock <= 0:
                flash(f'Product {item["name"]} is no longer available', 'error')
                return redirect(url_for('cart'))
            
            item_subtotal = item['price'] * item['quantity']
            subtotal += item_subtotal
            cart_for_db.append({
                'product_id': product_id,
                'product': product,
                'item': item,
                'subtotal': item_subtotal
            })
        
        # Calculate charges
        delivery_charges = {
            'standard': 0,
            'express': 150,
            'pickup': 0
        }
        delivery_charge = delivery_charges.get(delivery_option, 0)
        discount = 0
        points_to_redeem = 0
        
        # Apply loyalty points discount if available
        if current_user.loyalty_card and current_user.loyalty_card.points >= 100:
            # User can redeem up to 100 points for discount (10 NPR max discount)
            points_to_redeem = min(100, current_user.loyalty_card.points)
            discount = points_to_redeem / 10  # 10 points = 1 NPR
        
        total = subtotal + delivery_charge - discount
        
        # Create order
        order = Order(
            user_id=current_user.id,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code,
            delivery_option=delivery_option,
            payment_method=payment_method,
            subtotal=subtotal,
            delivery_charge=delivery_charge,
            discount=discount,
            total=total,
            payment_status='completed' if payment_method == 'cod' else 'pending',
            order_status='pending',
            points_redeemed=points_to_redeem
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add order items
        for item_data in cart_for_db:
            order_item = OrderItem(
                order_id=order.id,
                product_id=int(item_data['product_id']),
                product_name=item_data['item']['name'],
                product_price=item_data['item']['price'],
                quantity=item_data['item']['quantity'],
                subtotal=item_data['subtotal']
            )
            db.session.add(order_item)
            
            # Update stock
            product = item_data['product']
            product.stock -= item_data['item']['quantity']
        
        # Update loyalty points
        points_earned = int(subtotal / 10)  # 1 point per 10 NPR
        order.points_earned = points_earned
        
        if current_user.loyalty_card:
            # Deduct redeemed points first
            if points_to_redeem > 0:
                current_user.loyalty_card.points -= points_to_redeem
                # Log redemption transaction
                redeem_transaction = PointsTransaction(
                    user_id=current_user.id,
                    points=points_to_redeem,
                    type='redeem',
                    description=f'Order #{order.id} - Rs. {discount:.2f} discount'
                )
                db.session.add(redeem_transaction)
            
            # Add earned points
            current_user.loyalty_card.points += points_earned
            current_user.loyalty_card.update_tier()
            
            # Log points earned transaction
            points_transaction = PointsTransaction(
                user_id=current_user.id,
                points=points_earned,
                type='earn',
                description=f'Order #{order.id} - Rs. {subtotal}'
            )
            db.session.add(points_transaction)
        
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        session.modified = True
        
        flash(f'Order placed successfully! Order ID: {order.id}', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error placing order: {str(e)}', 'error')
        return redirect(url_for('checkout'))


@app.route('/order/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.get_or_404(order_id)
    
    # Check authorization
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    return render_template('order_confirmation.html', order=order)


@app.route('/my_orders')
@login_required
def my_orders():
    """User's order history"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)


@app.route('/pay-with-khalti', methods=['POST'])
@login_required
def pay_with_khalti():
    """Initiate Khalti payment for cart"""
    
    if not session.get('cart'):
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    try:
        # Get checkout form data from POST
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        delivery_option = request.form.get('delivery_option', 'standard')
        
        # Validate
        if not all([full_name, email, phone, address, city, postal_code]):
            flash('All fields are required', 'error')
            return redirect(url_for('checkout'))
        
        # Calculate totals
        subtotal = 0
        for product_id, item in session['cart'].items():
            product = Product.query.get(int(product_id))
            if not product or product.stock <= 0:
                flash(f'Product {item["name"]} is no longer available', 'error')
                return redirect(url_for('cart'))
            subtotal += item['price'] * item['quantity']
        
        # Calculate charges
        delivery_charges = {'standard': 0, 'express': 150, 'pickup': 0}
        delivery_charge = delivery_charges.get(delivery_option, 0)
        discount = 0
        points_to_redeem = 0
        
        # Apply loyalty discount
        if current_user.loyalty_card and current_user.loyalty_card.points >= 100:
            points_to_redeem = min(100, current_user.loyalty_card.points)
            discount = points_to_redeem / 10  # 10 points = 1 NPR
        
        total = subtotal + delivery_charge - discount
        
        # Store checkout details in session for post-payment verification
        session['checkout_data'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'city': city,
            'postal_code': postal_code,
            'delivery_option': delivery_option,
            'subtotal': subtotal,
            'delivery_charge': delivery_charge,
            'discount': discount,
            'total': total,
            'points_to_redeem': points_to_redeem
        }
        session.modified = True
        
        # Khalti API endpoint
        url = "https://a.khalti.com/api/v2/epayment/initiate/"
        
        # Prepare payload for Khalti
        payload = {
            "return_url": url_for('khalti_payment_success', _external=True),
            "website_url": url_for('home', _external=True),
            "amount": int(total * 100),  # Convert to paisa (1 rupee = 100 paisa)
            "purchase_order_id": f"ORDER_{current_user.id}_{int(datetime.utcnow().timestamp())}",
            "purchase_order_name": f"Saraswati Stationery Order",
            "customer_info": {
                "name": full_name,
                "email": email,
                "phone": phone
            }
        }
        
        headers = {
            "Authorization": f"Key {app.config['KHALTI_SECRET_KEY']}",
            "Content-Type": "application/json",
        }
        
        # Call Khalti API
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            flash('Failed to initiate Khalti payment. Please try again.', 'error')
            return redirect(url_for('checkout'))
        
        data = response.json()
        
        if 'payment_url' not in data:
            flash('Payment gateway error. Please try again.', 'error')
            return redirect(url_for('checkout'))
        
        # Redirect to Khalti payment page
        return redirect(data['payment_url'])
    
    except Exception as e:
        flash(f'Error initiating payment: {str(e)}', 'error')
        return redirect(url_for('checkout'))


@app.route('/payment-success')
@login_required
def khalti_payment_success():
    """Handle Khalti payment success - verify and create order"""
    
    # Get verification parameters from Khalti
    pidx = request.args.get('pidx')
    transaction_id = request.args.get('transaction_id')
    amount = request.args.get('amount')
    
    if not pidx:
        flash('Invalid payment response', 'error')
        return redirect(url_for('checkout'))
    
    try:
        # Verify payment with Khalti API - VERY IMPORTANT
        verify_url = "https://a.khalti.com/api/v2/epayment/lookup/"
        
        verify_payload = {
            "pidx": pidx
        }
        
        headers = {
            "Authorization": f"Key {app.config['KHALTI_SECRET_KEY']}",
            "Content-Type": "application/json",
        }
        
        verify_response = requests.post(verify_url, json=verify_payload, headers=headers)
        
        if verify_response.status_code != 200:
            flash('Payment verification failed', 'error')
            return redirect(url_for('checkout'))
        
        verify_data = verify_response.json()
        
        # Check if payment was successful
        if verify_data.get('status') != 'Completed':
            flash('Payment was not completed', 'error')
            return redirect(url_for('checkout'))
        
        # Payment verified successfully! Now create order
        checkout_data = session.get('checkout_data')
        cart = session.get('cart', {})
        
        if not checkout_data or not cart:
            flash('Session data missing. Please try again.', 'error')
            return redirect(url_for('checkout'))
        
        # Create order
        order = Order(
            user_id=current_user.id,
            full_name=checkout_data['full_name'],
            email=checkout_data['email'],
            phone=checkout_data['phone'],
            address=checkout_data['address'],
            city=checkout_data['city'],
            postal_code=checkout_data['postal_code'],
            delivery_option=checkout_data['delivery_option'],
            payment_method='khalti',
            subtotal=checkout_data['subtotal'],
            delivery_charge=checkout_data['delivery_charge'],
            discount=checkout_data['discount'],
            total=checkout_data['total'],
            payment_status='completed',
            order_status='pending',
            points_redeemed=checkout_data.get('points_to_redeem', 0)
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        for product_id, item in cart.items():
            product = Product.query.get(int(product_id))
            order_item = OrderItem(
                order_id=order.id,
                product_id=int(product_id),
                product_name=item['name'],
                product_price=item['price'],
                quantity=item['quantity'],
                subtotal=item['price'] * item['quantity']
            )
            db.session.add(order_item)
            
            # Update stock
            product.stock -= item['quantity']
        
        # Update loyalty points
        points_earned = int(checkout_data['subtotal'] / 10)
        order.points_earned = points_earned
        points_redeemed = checkout_data.get('points_to_redeem', 0)
        
        if current_user.loyalty_card:
            # Deduct redeemed points first
            if points_redeemed > 0:
                current_user.loyalty_card.points -= points_redeemed
                # Log redemption transaction
                redeem_transaction = PointsTransaction(
                    user_id=current_user.id,
                    points=points_redeemed,
                    type='redeem',
                    description=f'Khalti Order #{order.id} - Rs. {checkout_data["discount"]:.2f} discount'
                )
                db.session.add(redeem_transaction)
            
            # Add earned points
            current_user.loyalty_card.points += points_earned
            current_user.loyalty_card.update_tier()
            
            # Log earned points transaction
            points_transaction = PointsTransaction(
                user_id=current_user.id,
                points=points_earned,
                type='earn',
                description=f'Khalti Order #{order.id} - Rs. {checkout_data["subtotal"]}'
            )
            db.session.add(points_transaction)
        
        db.session.commit()
        
        # Clear session data
        session.pop('cart', None)
        session.pop('checkout_data', None)
        session.modified = True
        
        flash(f'Payment successful! Order ID: {order.id}', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    except Exception as e:
        flash(f'Error processing payment: {str(e)}', 'error')
        return redirect(url_for('checkout'))


@app.route('/payment-failed')
@login_required
def khalti_payment_failed():
    """Handle Khalti payment failure"""
    flash('Payment was cancelled or failed. Please try again.', 'warning')
    return redirect(url_for('checkout'))


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
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

@app.route('/admin/admin_dashboard')
@login_required
def admin_dashboard_redirect():
    if current_user.role != 'admin':
        flash("Access denied", "error")
        return redirect(url_for('dashboard'))

    return redirect(url_for('admin_dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        # Admins should go to admin dashboard instead
        return redirect(url_for('admin_dashboard'))
    
    # Ensure user has a loyalty card
    if not current_user.loyalty_card:
        loyalty_card = LoyaltyCard(user_id=current_user.id)
        db.session.add(loyalty_card)
        db.session.commit()
    
    return render_template('user/dashboard.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add_sale', methods=['POST'])
@login_required
def add_sale():
    if not current_user.is_admin:
        abort(403)

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

    # Create Points Transaction Record
    points_transaction = PointsTransaction(
        user_id=user.id,
        points=points_earned,
        type='earn',
        description=f'Sale of Rs. {amount} - {items}'
    )
    db.session.add(points_transaction)

    db.session.commit()

    flash(f'Sale recorded! {points_earned} points added to {user.username}.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        abort(403)

    products = Product.query.all()
    return render_template('admin/admin_products.html', products=products)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            price = request.form.get('price', '0')
            stock = request.form.get('stock', '0')
            category = request.form.get('category', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validate required fields
            if not name or not price or not stock:
                flash('Name, price, and stock are required!', 'danger')
                return render_template('admin/add_product.html')
            
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                try:
                    image_filename = save_product_image(file)
                except ValueError as e:
                    flash(str(e), 'danger')
                    return render_template('admin/add_product.html')
            
            # Create product
            product = Product(
                name=name,
                price=float(price),
                stock=int(stock),
                category=category,
                description=description,
                image_filename=image_filename
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
            return render_template('admin/add_product.html')

    return render_template('admin/add_product.html')


@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        try:
            # Update basic fields
            product.name = request.form.get('name', '').strip()
            product.price = float(request.form.get('price', product.price))
            product.stock = int(request.form.get('stock', product.stock))
            product.category = request.form.get('category', '').strip()
            product.description = request.form.get('description', '').strip()
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    try:
                        product.image_filename = save_product_image(file, product.image_filename)
                    except ValueError as e:
                        flash(str(e), 'danger')
                        return render_template('admin/edit_product.html', product=product)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')

    return render_template('admin/edit_product.html', product=product)



@app.route('/admin/delete_product/<int:id>')
@login_required
def delete_product(id):
    if not current_user.is_admin:
        abort(403)

    product = Product.query.get_or_404(id)
    
    # Delete product image if it exists
    delete_product_image(product.image_filename)
    
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    from sqlalchemy import func
    from datetime import datetime, timedelta
    import json

    # KPI Metrics
    total_customers = User.query.filter_by(role='customer').count()
    
    # Count both manual sales and orders
    total_sales_manual = Sale.query.count()
    total_orders = Order.query.count()
    total_sales = total_sales_manual + total_orders
    
    # Calculate revenue from both Sales and Orders
    revenue_from_sales = db.session.query(func.sum(Sale.amount)).scalar() or 0
    revenue_from_orders = db.session.query(func.sum(Order.total)).filter(
        Order.payment_status == 'completed'
    ).scalar() or 0
    total_revenue = revenue_from_sales + revenue_from_orders
    
    active_cards = LoyaltyCard.query.count()

    # Monthly Revenue (current month)
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)
    
    monthly_revenue_sales = db.session.query(func.sum(Sale.amount)).filter(
        func.date(Sale.date) >= first_day_of_month
    ).scalar() or 0
    
    monthly_revenue_orders = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) >= first_day_of_month,
        Order.payment_status == 'completed'
    ).scalar() or 0
    
    monthly_revenue = monthly_revenue_sales + monthly_revenue_orders
    
    # Points Issued Today (sum of points from sales and orders today)
    today_sales = Sale.query.filter(
        func.date(Sale.date) == today
    ).all()
    today_orders = Order.query.filter(
        func.date(Order.created_at) == today,
        Order.payment_status == 'completed'
    ).all()
    
    points_issued_today = sum(int(sale.amount / 10) for sale in today_sales) + sum(order.points_earned for order in today_orders)

    # Total Products & Low Stock
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 10).count()

    # Sales Over Time (last 7 days) - Combined from Sales and Orders
    sales_by_date = {}
    for i in range(6, -1, -1):  # Last 7 days
        date = today - timedelta(days=i)
        
        daily_sales = db.session.query(func.sum(Sale.amount)).filter(
            func.date(Sale.date) == date
        ).scalar() or 0
        
        daily_orders = db.session.query(func.sum(Order.total)).filter(
            func.date(Order.created_at) == date,
            Order.payment_status == 'completed'
        ).scalar() or 0
        
        sales_by_date[date.strftime('%b %d')] = float(daily_sales + daily_orders)

    # Loyalty Tier Distribution
    silver_count = LoyaltyCard.query.filter_by(tier='Silver').count()
    gold_count = LoyaltyCard.query.filter_by(tier='Gold').count()
    platinum_count = LoyaltyCard.query.filter_by(tier='Platinum').count()

    # Recent Sales
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()

    return render_template(
        'admin/admin_dashboard.html',
        total_customers=total_customers,
        total_sales=total_sales,
        total_revenue=total_revenue,
        active_cards=active_cards,
        monthly_revenue=monthly_revenue,
        points_issued_today=points_issued_today,
        total_products=total_products,
        low_stock=low_stock,
        sales_by_date=json.dumps(sales_by_date),
        silver_count=silver_count,
        gold_count=gold_count,
        platinum_count=platinum_count,
        recent_sales=recent_sales
    )


@app.route('/admin/customers')
@login_required
def admin_customers():
    if not current_user.is_admin:
        abort(403)

    customers = User.query.filter_by(role='customer').all()
    return render_template('admin/customers.html', customers=customers)


@app.route('/admin/loyalty_cards')
@login_required
def admin_loyalty_cards():
    if not current_user.is_admin:
        abort(403)

    loyalty_cards = LoyaltyCard.query.all()
    return render_template('admin/loyalty_cards.html', loyalty_cards=loyalty_cards)


@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        abort(403)

    # Get all orders with user info
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_admin:
        abort(403)

    order = Order.query.get_or_404(order_id)
    status = request.form.get('order_status')
    tracking = request.form.get('tracking_number')
    carrier = request.form.get('carrier')
    notes = request.form.get('dispatcher_notes')

    if status:
        order.order_status = status
    if tracking is not None:
        order.tracking_number = tracking.strip() or None
    if carrier is not None:
        order.carrier = carrier.strip() or None
    if notes is not None:
        order.dispatcher_notes = notes.strip() or None

    if status == 'delivered':
        order.delivered_at = datetime.utcnow()
        order.delivery_confirmed = True

    db.session.commit()
    flash('Order updated successfully.', 'success')
    return redirect(url_for('admin_orders'))


@app.route('/order/<int:order_id>/confirm_delivery', methods=['POST'])
@login_required
def confirm_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    order.delivery_confirmed = True
    order.delivered_at = datetime.utcnow()
    order.order_status = 'delivered'
    db.session.commit()
    flash('Delivery confirmed. Thank you!', 'success')
    return redirect(url_for('order_confirmation', order_id=order.id))


@app.route('/admin/sales')
@login_required
def admin_sales():
    if not current_user.is_admin:
        abort(403)

    # Get both manual sales and orders
    sales = Sale.query.order_by(Sale.date.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/sales.html', sales=sales, orders=orders)


@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        abort(403)

    from sqlalchemy import func
    
    # Calculate totals from both Sales and Orders
    revenue_from_sales = db.session.query(func.sum(Sale.amount)).scalar() or 0
    revenue_from_orders = db.session.query(func.sum(Order.total)).filter(
        Order.payment_status == 'completed'
    ).scalar() or 0
    total_sales = revenue_from_sales + revenue_from_orders
    
    # Count transactions
    manual_sales_count = Sale.query.count()
    orders_count = Order.query.count()
    total_transactions = manual_sales_count + orders_count
    
    total_customers = User.query.filter_by(role='customer').count()
    
    return render_template('admin/reports.html', 
                          total_sales=total_sales,
                          total_transactions=total_transactions,
                          total_customers=total_customers)


@app.route('/admin/settings')
@login_required
def admin_settings():
    if not current_user.is_admin:
        abort(403)

    return render_template('admin/settings.html')


if __name__ == '__main__':
    if not os.path.exists('stationery.db'):
        with app.app_context():
            db.create_all()
            print("Database created.")
    app.run(debug=True)
