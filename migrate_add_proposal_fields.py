"""
Migration script to add new fields to TripProposal table:
- departure_location
- activities
- Boolean fields for marking information as final

For MariaDB/MySQL database
"""

from app import app
from traveltogetherapp.models import db

with app.app_context():
    # Add new columns to trip_proposal table
    # MariaDB/MySQL uses TINYINT(1) for BOOLEAN
    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN departure_location VARCHAR(100)"))
        print("Added departure_location column")
    except Exception as e:
        print(f"departure_location: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN activities TEXT"))
        print("Added activities column")
    except Exception as e:
        print(f"activities: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN departure_location_is_final INT(1) DEFAULT 0"))
        print("Added departure_location_is_final column")
    except Exception as e:
        print(f"departure_location_is_final: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN destination_is_final INT(1) DEFAULT 0"))
        print("Added destination_is_final column")
    except Exception as e:
        print(f"destination_is_final: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN budget_is_final TINYINT(1) DEFAULT 0"))
        print("Added budget_is_final column")
    except Exception as e:
        print(f"budget_is_final: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN dates_are_final TINYINT(1) DEFAULT 0"))
        print("Added dates_are_final column")
    except Exception as e:
        print(f"dates_are_final: {e}")

    try:
        db.session.execute(db.text("ALTER TABLE trip_proposal ADD COLUMN activities_are_final TINYINT(1) DEFAULT 0"))
        print("Added activities_are_final column")
    except Exception as e:
        print(f"activities_are_final: {e}")

    db.session.commit()
    print("\nMigration completed successfully!")
