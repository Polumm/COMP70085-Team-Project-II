# API search logic
from flask import Blueprint, render_template, request, current_app
import requests

search = Blueprint("search", __name__)


@search.route("/", methods=["GET", "POST"])
def movie_search():
    TMDB_API_KEY = current_app.config["TMDB_API_KEY"]
    BASE_URL = "https://api.themoviedb.org/3"

    genres_response = requests.get(
        f"{BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    )
    genres = (
        genres_response.json().get("genres", []) if genres_response.ok else []
    )

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "page": request.args.get("page", 1),
    }

    if request.method == "POST":
        filters = [
            "year",
            "primary_release_year",
            "region",
            "with_original_language",
        ]
        for f in filters:
            if request.form.get(f):
                params[f] = request.form.get(f)

        try:
            response = requests.get(
                f"{BASE_URL}/discover/movie", params=params
            )
            response.raise_for_status()
            movies_data = response.json()
            return render_template(
                "search.html",
                movies=movies_data.get("results", []),
                genres=genres,
            )
        except requests.RequestException as e:
            return render_template(
                "search.html",
                error=f"Error fetching movies: {str(e)}",
                genres=genres,
            )

    return render_template("search.html", genres=genres)
