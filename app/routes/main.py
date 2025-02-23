# Main routes
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
import requests

main = Blueprint("main", __name__)


@main.route("/")
def landing_page():
    # return "Hello, this is a test"
    return render_template("home.html")


@main.route("/home")
def home():
    return render_template("home.html", user=current_user)


@main.route("/profile")
def profile():
    return render_template("profile.html")


@main.route("/friends")
def friends():
    return render_template("friends.html")


@main.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@main.route("/saved")
def saved():
    return render_template("saved.html")


@main.route("/get-quote")
def get_quote():
    api_url = "https://quoteapi.pythonanywhere.com/quotes/"

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise error if the request fails
        data = response.json()

        # Extract the quotes
        if "Quotes" in data and isinstance(data["Quotes"], list) and len(data["Quotes"]) > 0:
            quotes_list = data["Quotes"][0]  # Extract the first list inside "Quotes"

            if quotes_list:  # Ensure there's at least one quote
                import random
                random_quote = random.choice(quotes_list)  # Pick a random quote

                return jsonify({
                    "quote": random_quote["quote"],
                    "movie": random_quote["movie_title"]
                })

        return jsonify({"error": "No movie quotes found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
