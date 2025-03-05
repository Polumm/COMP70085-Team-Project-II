# Initialize the app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from app.config import Config
import json

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = (
    "auth.login"  # Redirects unauthorized users to login page
)


def load_json_filter(s, default=None):
    """Custom Jinja filter to parse JSON strings into Python objects."""
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        return default


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["CHATBOT_URL"] = Config.CHATBOT_URL
    app.config["DB_SERVICE_URL"] = Config.DB_SERVICE_URL

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import models after db is initialized
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Jinja filter with the main app
    app.jinja_env.filters["load_json"] = load_json_filter
    
    # Import and register Blueprints
    from app.routes.main import main
    from app.routes.search import search
    from app.routes.auth import auth
    from app.routes.quotes import quote_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.profile import profile_bp
    from app.routes.friend_profile import friend_profile_bp


    app.register_blueprint(main, url_prefix="/")
    app.register_blueprint(search, url_prefix="/search")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(quote_bp, url_prefix="/")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(friend_profile_bp, url_prefix="/profile/friend")

    # Ensure tables are created
    with app.app_context():
        db.create_all()

    return app
