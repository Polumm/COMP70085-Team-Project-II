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

     # Fetch available languages from TMDB
    languages_response = requests.get(
        f"{BASE_URL}/configuration/languages?api_key={TMDB_API_KEY}"
    )
    if languages_response.ok:
        languages = languages_response.json()
        print(f"Languages Data: {languages}")  # DEBUGGING
    else:
        print("Failed to fetch languages")  # DEBUGGING
        languages = []
    
    # Initialize variables for template
    movies_data = {}
    current_page = 1
    total_pages = 1

    # Ensure `selected_filters` is always defined
    selected_filters = request.form.copy() if request.method == "POST" else {}

    # Start building the API parameters
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "page": request.args.get("page", 1),
    }

    if request.method == "POST":
        print(f"Form Data Received: {request.form}")

        # Handle general filters like year, etc.
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
        ]
        
        for f in filters:
            value = request.form.get(f)
            if value:
                params[f] = value  # Add the filter to params only if it's non-empty

        if request.form.get("sort_by"):
            params["sort_by"] = request.form.get("sort_by")

        # Handle Language Filter
        if request.form.get("with_original_language"):
            params["with_original_language"] = request.form.get("with_original_language")

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
        
    # Return only results if AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("results.html", movies=movies_data.get("results", []), current_page=current_page, total_pages=total_pages)

    # Always pass all required variables to the template
    return render_template(
        "search.html",
        movies=movies_data.get("results", []),
        genres=genres,
        languages=languages,
        selected_filters=selected_filters,  # Ensure selected filters are always available
        current_page=current_page,
        total_pages=total_pages
    )


