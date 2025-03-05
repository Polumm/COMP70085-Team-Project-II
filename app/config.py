# Configurations
import os
from dotenv import load_dotenv

# Only load .env in development mode (Optional)
if os.getenv("FLASK_ENV") == "development":
    load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your-api-key")
    CHATBOT_URL = os.getenv("CHATBOT_URL")
    DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")
