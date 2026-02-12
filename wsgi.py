"""
WSGI entry point for Gunicorn/Render deployment
"""
import os
from app import app, db

# Initialize database on startup
def create_app():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
    return app

# For Gunicorn
if __name__ == "__main__":
    app = create_app()
