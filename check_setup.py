"""
Database and Requirements Check Script for TravelTogether
This script verifies that all requirements are properly installed and configured.
"""

import sys
import importlib

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def check_database_connection():
    """Check if database connection works"""
    try:
        from app import app
        from traveltogetherapp.models import db, User
        
        with app.app_context():
            # Try a simple query
            result = db.session.execute(db.text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_tables_exist():
    """Check if required tables exist in database"""
    try:
        from app import app
        from traveltogetherapp.models import db
        
        with app.app_context():
            tables = ['user', 'trip_proposal', 'participation', 'message', 'meetup']
            existing_tables = db.inspect(db.engine).get_table_names()
            
            all_exist = True
            for table in tables:
                if table in existing_tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' does NOT exist")
                    all_exist = False
            
            return all_exist
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def main():
    print("=" * 70)
    print("TRAVELTOGETHER - SYSTEM CHECK")
    print("=" * 70)
    
    print("\n1. Checking Python version...")
    print(f"   Python {sys.version}")
    
    print("\n2. Checking required packages...")
    packages = {
        'flask': 'flask',
        'flask-login': 'flask_login',
        'flask-sqlalchemy': 'flask_sqlalchemy',
        'sqlalchemy': 'sqlalchemy',
        'werkzeug': 'werkzeug',
        'wtforms': 'wtforms',
        'pymysql': 'pymysql',
        'email-validator': 'email_validator',
    }
    
    all_installed = True
    for package, import_name in packages.items():
        if not check_package(package, import_name):
            all_installed = False
    
    if not all_installed:
        print("\n⚠️  Some packages are missing. Install them with:")
        print("   pip install -r requirements.txt")
        return
    
    print("\n3. Checking database connection...")
    if not check_database_connection():
        print("\n⚠️  Database connection failed. Check your config.py settings.")
        return
    
    print("\n4. Checking database tables...")
    if not check_tables_exist():
        print("\n⚠️  Some tables are missing. Run: python init_db.py")
        return
    
    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED! Your application is ready to run.")
    print("=" * 70)
    print("\nTo start the application, run: python app.py")

if __name__ == "__main__":
    main()
