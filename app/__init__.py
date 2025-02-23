# Initialize the app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Redirects unauthorized users to login page


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models after db is initialized
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import and register Blueprints
    from app.routes.main import main
    from app.routes.search import search
    from app.routes.auth import auth
    from app.routes.quotes import quote_bp


    app.register_blueprint(main, url_prefix="/")
    app.register_blueprint(search, url_prefix="/search")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(quote_bp, url_prefix="/")

    # Ensure tables are created
    with app.app_context():
        db.create_all()

    return app
