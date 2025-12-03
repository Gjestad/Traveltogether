"""
Migration script to add start_date and end_date columns to trip_proposal table
"""
import sqlite3
from pathlib import Path

# Path to database
db_path = Path(__file__).parent / "instance" / "traveltogether.db"

print(f"Migrating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add start_date column
    cursor.execute("ALTER TABLE trip_proposal ADD COLUMN start_date DATE")
    print("✓ Added start_date column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ start_date column already exists")
    else:
        raise

try:
    # Add end_date column
    cursor.execute("ALTER TABLE trip_proposal ADD COLUMN end_date DATE")
    print("✓ Added end_date column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ end_date column already exists")
    else:
        raise

conn.commit()
conn.close()

print("\n✅ Migration completed successfully!")
