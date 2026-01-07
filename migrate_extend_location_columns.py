"""
Migration script to extend departure_location and destination columns from VARCHAR(100) to VARCHAR(255)
to accommodate longer OpenStreetMap addresses.

For MariaDB/MySQL database
"""

from app import app
from traveltogetherapp.models import db

with app.app_context():
    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal MODIFY COLUMN departure_location VARCHAR(255)"))
        print("Extended departure_location column to VARCHAR(255)")
    except Exception as e:
        print(f"departure_location: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal MODIFY COLUMN destination VARCHAR(255)"))
        print("Extended destination column to VARCHAR(255)")
    except Exception as e:
        print(f"destination: {e}")

    db.session.commit()
    print("\nMigration completed successfully!")
