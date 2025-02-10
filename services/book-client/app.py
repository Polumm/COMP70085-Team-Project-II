from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# Read Book API URL from environment variable or use default
BOOK_API_URL = os.getenv("BOOK_API_URL", "http://localhost:5000/books/search")


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Book Client API!"})


# Consume the Book API and filter books by genre
@app.route("/search", methods=["GET"])
def search_books():
    genre = request.args.get("genre")

    if not genre:
        return jsonify(
            {"error": "Please provide a genre query parameter"}
        ), 400

    try:
        # Call the Book API
        response = requests.get(f"{BOOK_API_URL}?genre={genre}")
        if response.status_code == 200:
            books = response.json()
            # Return the first matching book
            if books:
                return jsonify(books[0])
            return jsonify({"error": "No books found in this genre"}), 404
        else:
            return jsonify(
                {"error": "Failed to retrieve data from Book API"}
            ), 500

    except requests.exceptions.RequestException as e:
        return jsonify(
            {"error": "Service unavailable", "details": str(e)}
        ), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
