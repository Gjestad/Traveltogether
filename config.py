import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecret")
    
    # Database configuration for UC3M lab infrastructure
    # Format: mysql+pymysql://26_webapp_XX:PASSWORD@mysql.lab.it.uc3m.es/26_webapp_XXa
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', '26_webapp_34')}:{os.getenv('DB_PASS', 'EfS4pvUh')}"
        f"@{os.getenv('DB_HOST', 'mysql.lab.it.uc3m.es')}/{os.getenv('DB_NAME', '26_webapp_34a')}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

