import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecret")
    
    # UC3M MariaDB credentials (from Telematic Engineering Department)
    # Username: 26_webapp_34
    # Password: EfS4pvUh
    # Available databases: 26_webapp_34a, 26_webapp_34b, 26_webapp_34c, 26_webapp_34d
    # Note: Only accessible from UC3M lab computers or virtual lab at https://aulavirtual.lab.it.uc3m.es/
    
    # Database configuration
    DB_USER = os.getenv('DB_USER', '26_webapp_34')
    DB_PASS = os.getenv('DB_PASS', 'EfS4pvUh')
    DB_HOST = os.getenv('DB_HOST', 'mysql.lab.it.uc3m.es')
    DB_NAME = os.getenv('DB_NAME', '26_webapp_34a')  # Choose: 34a, 34b, 34c, or 34d
    
    # Use SQLite for development, MySQL in production
    if os.getenv("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///traveltogether.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

