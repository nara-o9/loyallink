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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def stock_status(self):
        if self.stock == 0:
            return "Out of Stock"
        elif self.stock < 10:
            return "Low Stock"
        return "In Stock"
