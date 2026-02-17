from app import app, db, Order
from sqlalchemy import inspect, text

"""
Run this script once to add delivery/tracking columns to the existing SQLite DB.
Usage (from project root):
  & '.venv/Scripts/python.exe' create_order_columns.py
"""

with app.app_context():
    inspector = inspect(db.engine)
    table_name = Order.__tablename__ if hasattr(Order, '__tablename__') else 'order'
    try:
        existing = [c['name'] for c in inspector.get_columns(table_name)]
    except Exception as e:
        print('Could not inspect table:', table_name, e)
        existing = []

    statements = []
    if 'tracking_number' not in existing:
        statements.append(f"ALTER TABLE \"{table_name}\" ADD COLUMN tracking_number TEXT;")
    if 'carrier' not in existing:
        statements.append(f"ALTER TABLE \"{table_name}\" ADD COLUMN carrier TEXT;")
    if 'delivered_at' not in existing:
        statements.append(f"ALTER TABLE \"{table_name}\" ADD COLUMN delivered_at DATETIME;")
    if 'delivery_confirmed' not in existing:
        statements.append(f"ALTER TABLE \"{table_name}\" ADD COLUMN delivery_confirmed BOOLEAN DEFAULT 0;")
    if 'dispatcher_notes' not in existing:
        statements.append(f"ALTER TABLE \"{table_name}\" ADD COLUMN dispatcher_notes TEXT;")

    if not statements:
        print('All delivery columns already exist.')
    else:
        for s in statements:
            print('Running:', s)
            with db.engine.connect() as conn:
                conn.execute(text(s))
        print('Done adding columns.')
