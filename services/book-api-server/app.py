from flask import Flask, jsonify, request
from books import books  # Importing book data from books.py

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Hi! Welcome to the Book API!"})


# Get all books
@app.route("/books", methods=["GET"])
def get_books():
    return jsonify(books)


# Get a single book by ID
@app.route("/books/<int:book_id>", methods=["GET"])
def get_book_by_id(book_id):
    book = next((book for book in books if book["id"] == book_id), None)
    if book:
        return jsonify(book)
    return jsonify({"error": "Book not found"}), 404


# Filter books by genre
@app.route("/books/search", methods=["GET"])
def search_books():
    genre = request.args.get("genre")
    if genre:
        filtered_books = [
            book for book in books if genre.lower() in book["genre"].lower()
        ]
        return jsonify(filtered_books)
    return jsonify({"error": "Please provide a genre query parameter"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
