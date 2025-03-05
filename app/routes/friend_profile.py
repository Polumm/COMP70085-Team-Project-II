from flask import Blueprint, render_template, request, flash
import requests
import os
from app.routes.auth import login_required

friend_profile_bp = Blueprint("friend_profile", __name__)
DB_SERVICE_URL = os.getenv("DB_SERVICE_URL", "http://localhost:6003")


@friend_profile_bp.route("/<username>")
@login_required
def friend_profile(username):
    """Display a friend's saved movies."""
    saved_movies = []

    try:
        # First step: Get the user_id for the username
        user_response = requests.get(f"{DB_SERVICE_URL}/users/by-username",
                                     params={"username": username},
                                     timeout=5)

        user_id = None
        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data.get("id")

        # If we can't find the user ID through the API, try another approach
        if not user_id:
            # Fallback: Get all users and find the matching username
            all_users_response = requests.get(f"{DB_SERVICE_URL}/users", timeout=5)
            if all_users_response.status_code == 200:
                all_users = all_users_response.json()
                for user in all_users:
                    if user.get("username") == username:
                        user_id = user.get("id")
                        break

        # Second step: Get the saved movies using the user_id
        if user_id:
            movie_response = requests.get(f"{DB_SERVICE_URL}/movies/list",
                                          params={"user_id": user_id},
                                          timeout=5)

            if movie_response.status_code == 200:
                movie_data = movie_response.json()
                saved_movies = movie_data.get("saved_movies", [])

                # Process poster paths
                for movie in saved_movies:
                    if movie.get("poster_path") and not movie["poster_path"].startswith("http"):
                        movie["poster_path"] = f"https://image.tmdb.org/t/p/w200{movie['poster_path']}"
            else:
                flash(f"Failed to load {username}'s saved movies. Status: {movie_response.status_code}", "error")
        else:
            flash(f"Could not find user ID for {username}", "error")

    except requests.RequestException as e:
        flash(f"Error loading {username}'s movies: {str(e)}", "error")

    return render_template("friend_profile.html", username=username, saved_movies=saved_movies)