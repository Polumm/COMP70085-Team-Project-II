from flask import Blueprint, render_template, request, current_app, session, redirect, url_for
import requests
import os

search = Blueprint("search", __name__)

DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")

@search.route("/", methods=["GET", "POST"])
def movie_search():
    TMDB_API_KEY = current_app.config["TMDB_API_KEY"]
    BASE_URL = "https://api.themoviedb.org/3"

    # ✅ Get logged-in user ID from session
    user_id = session.get("user_id")  # Ensure session contains user_id

    if not user_id:
        return redirect(url_for("auth.login"))  # Redirect if not logged in

    # Get genres list from TMDB
    genres_response = requests.get(
        f"{BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    )
    genres = genres_response.json().get("genres", []) if genres_response.ok else []

    # Fetch available languages from TMDB
    languages_response = requests.get(
        f"{BASE_URL}/configuration/languages?api_key={TMDB_API_KEY}"
    )
    languages = languages_response.json() if languages_response.ok else []

    # Initialize template variables
    movies_data = {}
    current_page = 1
    total_pages = 1
    selected_genres = []  # Initialize to ensure it's always defined

    # Initialize `selected_filters` properly
    selected_filters = {}

    # Start building the API parameters
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "page": request.args.get("page", 1),
    }

    if request.method == "POST":
        print(f"Form Data Received: {request.form}")

        # Define filter keys to persist
        filters = [
            "year", 
            "primary_release_year",
            "release_date.gte", 
            "release_date.lte",
            "vote_average.gte",
            "vote_average.lte",
            "vote_count.gte", 
            "with_runtime.gte", 
            "with_runtime.lte", 
            "with_original_language", 
            "sort_by"
        ]
        
        # Store filters in `params` and `selected_filters`
        for f in filters:
            value = request.form.get(f)
            if value:
                params[f] = value  
                selected_filters[f] = value  # Ensure it persists

        # Handle multi-select genres
        selected_genres = request.form.getlist("with_genres")  
        if selected_genres:
            params["with_genres"] = ",".join(selected_genres)
        
        # Save selected genres separately for form repopulation
        selected_filters["with_genres"] = selected_genres  

        # Debugging output
        print(f"Final Params: {params}")

        # Try fetching data from TMDB
        try:
            response = requests.get(f"{BASE_URL}/discover/movie", params=params)
            print(f"API Request URL: {response.url}")

            response.raise_for_status()
            movies_data = response.json()
            current_page = movies_data.get("page", 1)
            total_pages = movies_data.get("total_pages", 1)
        except requests.RequestException as e:
            return render_template(
                "search.html",
                error=f"Error fetching movies: {str(e)}",
                genres=genres,
                languages=languages,
                selected_filters=selected_filters,
                current_page=current_page,
                total_pages=total_pages,
                movies=[],
                user_id=user_id
            )

    return render_template(
        "search.html",
        movies=movies_data.get("results", []),
        genres=genres,
        languages=languages,
        selected_filters=selected_filters,
        current_page=current_page,
        total_pages=total_pages,
        user_id=user_id,
        DB_SERVICE_URL=DB_SERVICE_URL
    )
