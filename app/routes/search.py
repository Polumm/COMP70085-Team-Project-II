from flask import Blueprint, render_template, request, current_app
import requests

search = Blueprint("search", __name__)

@search.route("/", methods=["GET", "POST"])
def movie_search():
    TMDB_API_KEY = current_app.config["TMDB_API_KEY"]
    BASE_URL = "https://api.themoviedb.org/3"

    # Get genres list from TMDB
    genres_response = requests.get(
        f"{BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    )
    genres = genres_response.json().get("genres", []) if genres_response.ok else []

    # Initialize variables for template
    movies_data = {}
    current_page = 1
    total_pages = 1

    # Start building the API parameters
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "page": request.args.get("page", 1),
    }

    if request.method == "POST":
        print(f"Form Data Received: {request.form}")

        # Handle general filters like year, region, etc.
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
            "region"
        ]
        
        for f in filters:
            value = request.form.get(f)
            if value:
                params[f] = value  # Add the filter to params only if it's non-empty

        # Handle Sorting (sort_by)
        if request.form.get("sort_by"):
            params["sort_by"] = request.form.get("sort_by")

        # Handle multiple genres selection
        genres = request.form.getlist("with_genres")
        if genres:
            params["with_genres"] = ",".join([str(genre) for genre in genres])  # Join selected genres by commas
        else:
            print("No genre selected!")  # Debugging

        print(f"Final Params: {params}")  # Debugging
        
        # Try to get the response from TMDB API with the constructed parameters
        try:
            response = requests.get(f"{BASE_URL}/discover/movie", params=params)
            print(f"API Request URL: {response.url}")  # Debugging the full request URL

            response.raise_for_status()  # Check for errors in the response
            movies_data = response.json()
            current_page = movies_data.get("page", 1)
            total_pages = movies_data.get("total_pages", 1)
        except requests.RequestException as e:
            return render_template(
                "search.html",
                error=f"Error fetching movies: {str(e)}",
                genres=genres,
                current_page=current_page,
                total_pages=total_pages,
                movies=[]
            )

    # Always pass all required variables to the template
    return render_template(
        "search.html",
        movies=movies_data.get("results", []),
        genres=genres,  # Pass genres to the template
        current_page=current_page,
        total_pages=total_pages
    )
