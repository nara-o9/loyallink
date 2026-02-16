from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create new admin
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password=generate_password_hash("admin123"),  # choose a secure password
        role="admin"
    )
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created successfully!")
