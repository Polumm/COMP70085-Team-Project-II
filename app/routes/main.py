# Main routes
from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from flask import (
    session,
    flash,
    redirect,
    url_for,
)

main = Blueprint("main", __name__)


@main.route("/")
def landing_page():
    return render_template("home.html", user=current_user)


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
@login_required
def chatbot():
    chatbot_url = current_app.config.get("CHATBOT_URL")
    token = session.get("token", None)

    # Append the token as a query parameter
    iframe_url = f"{chatbot_url}?token={token}"
    return render_template("bot_multisession.html", chatbot_url=iframe_url)


@main.route("/saved")
def saved():
    return render_template("saved.html")
