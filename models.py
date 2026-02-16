from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='customer') # 'admin' or 'customer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='user', lazy=True)
    loyalty_card = db.relationship('LoyaltyCard', backref='user', uselist=False, lazy=True)
    
    @property
    def is_admin(self):
        return self.role == 'admin'

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False) # In NPR
    items = db.Column(db.String(500), nullable=True) # Description of items
    date = db.Column(db.DateTime, default=datetime.utcnow)

class LoyaltyCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(50), default='Silver') # Silver, Gold, Platinum

    def update_tier(self):
        if self.points >= 1000:
            self.tier = 'Platinum'
        elif self.points >= 500:
            self.tier = 'Gold'
        else:
            self.tier = 'Silver'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))  # Stores uploaded image filename
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def stock_status(self):
        if self.stock == 0:
            return "Out of Stock"
        elif self.stock < 10:
            return "Low Stock"
        return "In Stock"
    
    def get_image_url(self):
        """Returns the image URL or a placeholder"""
        if self.image_filename:
            return f"/static/uploads/products/{self.image_filename}"
        return "/static/uploads/products/placeholder.svg"


class PointsTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'earn' or 'redeem'
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='points_transactions')


class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points_cost = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100))  # 'discount', 'gift', 'exclusive', etc.
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Reward {self.name}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    
    # Address
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    
    # Order Details
    subtotal = db.Column(db.Float, nullable=False)
    delivery_charge = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    
    # Delivery & Payment
    delivery_option = db.Column(db.String(50), default='standard')  # 'standard', 'express', 'pickup'
    payment_method = db.Column(db.String(50), default='cod')  # 'cod', 'online', 'bank_transfer'
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed'
    order_status = db.Column(db.String(50), default='pending')  # 'pending', 'processing', 'shipped', 'delivered', 'cancelled'
    
    # Loyalty
    points_earned = db.Column(db.Integer, default=0)
    points_redeemed = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    product_name = db.Column(db.String(200), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='order_items')

