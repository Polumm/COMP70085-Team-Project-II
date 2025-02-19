# Initialize the app
from flask import Flask

# Import routes and config
from app.routes.main import main
from app.routes.search import search
from app.config import Config

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(main, url_prefix="/")
    app.register_blueprint(search, url_prefix="/search")

    return app
