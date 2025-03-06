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
    user_id = session.get("user_id")

    if not user_id:
        from flask import flash
        flash("Please log in first.")  # Added danger category for red color
        return redirect(url_for("auth.login", next=request.url))  # Redirect if not logged in   
    
    # Get genres and languages from TMDB
    genres_response = requests.get(f"{BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US")
    genres = genres_response.json().get("genres", []) if genres_response.ok else []

    languages_response = requests.get(f"{BASE_URL}/configuration/languages?api_key={TMDB_API_KEY}")
    languages = languages_response.json() if languages_response.ok else []

    languages = sorted(languages, key=lambda x: x["english_name"])

    # ✅ Initialize variables
    current_page = 1  
    total_pages = 1  
    movies = []  
    selected_filters = {}

    # ✅ Capture page number properly
    page_number = int(request.args.get("page", 1))
    print(f"🟡 Current Page Requested: {page_number}")  # Debugging

    # ✅ Define filter keys
    filter_keys = [
        "year", "primary_release_year", "release_date.gte", "release_date.lte",
        "vote_average.gte", "vote_average.lte", "vote_count.gte", 
        "with_runtime.gte", "with_runtime.lte", "with_original_language", "sort_by"
    ]

    # ✅ Start building API parameters
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "page": page_number,  # ✅ Ensure correct page number is used
    }

    # ✅ **Only fetch movies if user searched (`POST`) or paginated (`GET` with filters)**
    has_searched = request.method == "POST" or any(request.args.get(k) for k in filter_keys)

    if has_searched:
        print(f"🟡 Fetching movies for Page: {page_number}")  # Debugging

        # ✅ Capture filters from POST (Search) and GET (Pagination)
        if request.method == "POST":
            print(f"🟡 Form Data Received: {request.form}")

            for key in filter_keys:
                value = request.form.get(key)
                if value:
                    params[key] = value
                    selected_filters[key] = value  # ✅ Store for template repopulation

            # ✅ Handle multi-select genres properly
            selected_filters["with_genres"] = request.form.getlist("with_genres")
            if selected_filters["with_genres"]:
                params["with_genres"] = ",".join(selected_filters["with_genres"])

        elif request.args.get("page"):  # ✅ Handle Pagination (Keep Previous Filters)
            print(f"🟡 Paginating - Keeping previous filters from GET: {request.args}")

            for key in filter_keys:
                value = request.args.get(key)
                if value:
                    params[key] = value
                    selected_filters[key] = value

            # ✅ Handle multi-select genres in pagination
            selected_filters["with_genres"] = request.args.getlist("with_genres")
            if selected_filters["with_genres"]:
                params["with_genres"] = ",".join(selected_filters["with_genres"])

        print(f"🟡 Final API Parameters: {params}")  # Debugging

        # ✅ Fetch movies from TMDB
        try:
            response = requests.get(f"{BASE_URL}/discover/movie", params=params)
            print(f"🟢 API Request URL: {response.url}")  # Debugging

            response.raise_for_status()
            movies_data = response.json()

            # ✅ Extract movies and pagination safely
            current_page = movies_data.get("page", page_number)
            total_pages = movies_data.get("total_pages", 1)
            movies = movies_data.get("results", [])

            print(f"🟢 Movies Retrieved for Page {current_page}: {len(movies)} movies")  # Debugging

        except requests.RequestException as e:
            print(f"🔴 Error fetching movies: {str(e)}")
            return render_template(
                "search.html",
                error=f"Error fetching movies: {str(e)}",
                genres=genres,
                languages=languages,
                selected_filters=selected_filters,
                current_page=current_page,
                total_pages=total_pages,
                movies=[],  # ✅ Empty movies list if there's no search
                user_id=user_id
            )

    # ✅ Render the template with movie data
    return render_template(
        "search.html",
        movies=movies,
        genres=genres,
        languages=languages,
        selected_filters=selected_filters,
        current_page=current_page,
        total_pages=total_pages,
        user_id=user_id,
        DB_SERVICE_URL=DB_SERVICE_URL
    )
