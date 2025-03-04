# Main routes
from flask import Blueprint, render_template
from flask_login import current_user
from app.routes.auth import login_required
from app.routes.chatbot import multisession_chat

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def landing_page():
    return render_template("landingpage.html", user=current_user)


@main.route("/home")
@login_required
def home():
    return render_template("home.html", user=current_user)


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@main.route("/friends")
@login_required
def friends():
    return render_template("friends.html")


@main.route("/chatbot")
@login_required
def chatbot():
    return multisession_chat()


