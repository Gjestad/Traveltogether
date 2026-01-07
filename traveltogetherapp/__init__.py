# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db, User
from . import models  # Ensure models are imported

# Set up login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    """Load user from database for login."""
    return db.session.get(User, int(user_id))


# Create Flask application
def create_app():
    """Oppretter og konfigurerer Flask-applikasjonen."""
    base_dir = os.path.dirname(__file__)
    template_dir = os.path.join(base_dir, "..", "templates")
    static_dir = os.path.join(base_dir, "..", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )

    # Read configuration script
    app.config.from_object("config.Config")

    # Connect database and login manager
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprint modules
    from .auth import auth_bp
    from .proposals import proposals_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(proposals_bp)

    # User gets sendt to index page/standard route
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
