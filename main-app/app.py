from flask import Flask, render_template, request
import requests

app = Flask(__name__,
            template_folder='src/templates',
            static_folder='src/static')

@app.route('/')
def landing_page():
    return "Hello, this is a test"
    #return render_template('landing_page.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/friends')
def friends():
    return render_template('friends.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    TMDB_API_KEY = "your-api-key" 
    BASE_URL = "https://api.themoviedb.org/3/discover/movie"
    
    # Auto populate data from API
    # Get genres list for the filter
    genres_response = requests.get(
        f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    )
    genres = genres_response.json().get('genres', []) if genres_response.ok else []
    
    # Get languages
    languages_response = requests.get(
        f"{BASE_URL}/configuration/languages?api_key={TMDB_API_KEY}"
    )
    languages = languages_response.json() if languages_response.ok else []
    
    # Get regions/countries
    regions_response = requests.get(
        f"{BASE_URL}/configuration/countries?api_key={TMDB_API_KEY}"
    )
    regions = regions_response.json() if regions_response.ok else []

    # Base parameters
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'include_adult': False,
        'page': request.args.get('page', 1)
    }
    
    if request.method == 'POST':
        # Basic filters
        basic_filters = [
            'year',
            'primary_release_year',
            'region',
            'with_original_language'
        ]
        
        # Range filters
        range_filters = {
            'vote_average': ('vote_average.gte', 'vote_average.lte'),
            'vote_count': ('vote_count.gte', 'vote_count.lte'),
            'runtime': ('with_runtime.gte', 'with_runtime.lte'),
            'primary_release_date': ('primary_release_date.gte', 'primary_release_date.lte'),
            'release_date': ('release_date.gte', 'release_date.lte')
        }
        
        # List filters (comma/pipe separated)
        list_filters = [
            'with_cast',
            'with_crew',
            'with_people',
            'with_companies',
            'with_genres',
            'with_keywords'
        ]
        
        # Process basic filters
        for filter_name in basic_filters:
            if request.form.get(filter_name):
                params[filter_name] = request.form.get(filter_name)
        
        # Process range filters
        for base_name, (min_param, max_param) in range_filters.items():
            min_value = request.form.get(f"{base_name}_min")
            max_value = request.form.get(f"{base_name}_max")
            if min_value:
                params[min_param] = min_value
            if max_value:
                params[max_param] = max_value
        
        # Process list filters
        for filter_name in list_filters:
            if request.form.get(filter_name):
                params[filter_name] = request.form.get(filter_name)
        
        # Handle sort_by
        if request.form.get('sort_by'):
            params['sort_by'] = request.form.get('sort_by')

        try:
            response = requests.get(f"{BASE_URL}/discover/movie", params=params)
            response.raise_for_status()
            movies_data = response.json()
            return render_template(
                'search.html',
                movies=movies_data.get('results', []),
                current_page=movies_data.get('page', 1),
                total_pages=movies_data.get('total_pages', 1),
                genres=genres,
                languages=languages,
                regions=regions
            )
        except requests.RequestException as e:
            error = f"Error fetching movies: {str(e)}"
            return render_template('search.html', 
                                error=error, 
                                genres=genres,
                                languages=languages,
                                regions=regions)
            
    # GET request - just show the search form with populated options
    return render_template('search.html', 
                         genres=genres,
                         languages=languages,
                         regions=regions)

@app.route('/saved')
def saved():
    return render_template('saved.html')

if __name__ == '__main__':
    print("Starting Flask app...")  # Debug print
    app.run(debug=True, port=5000)