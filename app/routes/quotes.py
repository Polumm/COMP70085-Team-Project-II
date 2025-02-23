import requests
import random
from flask import Blueprint, jsonify

quote_bp = Blueprint("quote", __name__)

# 🎯 Define API URL as a constant
API_URL = "https://quoteapi.pythonanywhere.com/quotes/"

def fetch_quotes():
    """Fetch quotes from API and filter only movie quotes."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Ensure valid response
        if "Quotes" not in data or not data["Quotes"]:
            return []

        # Extract the list of quotes
        quotes_list = data["Quotes"][0]

        # **Filter out TV Series quotes**
        movie_quotes = [q for q in quotes_list if "TV Series" not in q.get("movie_title", "")]

        return movie_quotes

    except requests.RequestException as e:
        print(f"🚨 Error fetching quotes: {e}")
        return []

@quote_bp.route("/get-quote")
def get_quote():
    """Returns a random movie quote (excluding TV Series)."""
    movie_quotes = fetch_quotes()

    if not movie_quotes:
        return jsonify({"error": "⚠️ No valid movie quotes available"}), 404

    # Pick a random movie quote
    quote = random.choice(movie_quotes)

    return jsonify({
        "quote": quote["quote"],
        "movie_title": quote["movie_title"],
        "author": quote.get("author", "Unknown")
    })
