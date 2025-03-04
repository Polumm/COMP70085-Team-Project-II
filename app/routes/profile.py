from flask import Blueprint, render_template, session, current_app, flash
import requests
import os
from app.routes.auth import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def user_profile():
    user_id = session.get('user_id')
    username = session.get('username')

    # Use the environment variable directly
    DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")

    # Fetch saved movies from the database service
    saved_movies = []
    try:
        if DB_SERVICE_URL:
            response = requests.get(f"{DB_SERVICE_URL}/movies/list?user_id={user_id}", timeout=5)
            if response.status_code == 200:
                saved_movies = response.json().get('saved_movies', [])

                # Process poster paths to ensure they're fully qualified URLs
                for movie in saved_movies:
                    if movie.get('poster_path') and not movie['poster_path'].startswith('http'):
                        movie['poster_path'] = f"https://image.tmdb.org/t/p/w200{movie['poster_path']}"
    except requests.RequestException as e:
        flash(f"Couldn't load saved movies: {str(e)}", "error")

    return render_template(
        "profile.html",
        saved_movies=saved_movies,
        user_id=user_id,
        DB_SERVICE_URL=DB_SERVICE_URL
    )