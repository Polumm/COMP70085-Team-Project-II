# Main routes
from flask import Blueprint, render_template
from flask_login import login_required, current_user

main = Blueprint("main", __name__)


@main.route("/")
def landing_page():
    # return "Hello, this is a test"
    return render_template("home.html")


@main.route("/home")
@login_required
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
