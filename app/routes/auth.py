from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    g,
    current_app,
    request,
)
from app.forms import LoginForm, SignupForm
from functools import wraps
import requests
import jwt
import os
from flask import current_app
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash

# Blueprint Configuration
auth = Blueprint("auth", __name__)

# Environment Variables
DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")


# ----------------------------------------------------
# JWT Helpers
# ----------------------------------------------------


def generate_jwt(username, expires_in=3600):
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    secret_key = current_app.config["SECRET_KEY"]  # Access from Flask config
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token):
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = session.get("token", None)
        if not token:
            flash("Please log in first.")
            return redirect(url_for("auth.login"))

        payload = decode_jwt(token)
        if not payload:
            flash("Session expired. Please log in again.")
            session.pop("token", None)
            return redirect(url_for("auth.login"))

        g.username = payload["username"]
        return func(*args, **kwargs)

    return wrapper


# ----------------------------------------------------
# Login Route
# ----------------------------------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Call DB microservice to authenticate user
        try:
            resp = requests.get(
                f"{DB_SERVICE_URL}/users/{username}", timeout=5
            )
            if resp.status_code == 200:
                user_data = resp.json()
                if check_password_hash(user_data["password_hash"], password):
                    # Generate JWT and store in session
                    token = generate_jwt(username)
                    session["token"] = token
                    flash("Login successful!", "success")
                    return redirect(url_for("main.home"))
                else:
                    flash("Invalid credentials.", "danger")
            else:
                flash("User not found.", "danger")
        except requests.exceptions.RequestException:
            flash("Error contacting user service.", "danger")

    return render_template("login.html", form=form)


# ----------------------------------------------------
# Signup Route
# ----------------------------------------------------
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.signup"))

        # Call DB microservice to create user
        try:
            resp = requests.post(
                f"{DB_SERVICE_URL}/users",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                },
                timeout=5,
            )
            if resp.status_code == 201:
                flash("Account created! You can now log in.", "success")
                return redirect(url_for("auth.login"))
            else:
                err_data = resp.json()
                flash(err_data.get("error", "Registration failed."), "danger")
        except requests.exceptions.RequestException:
            flash("Error contacting user service.", "danger")

    return render_template("signup.html", form=form)


# ----------------------------------------------------
# Logout Route
# ----------------------------------------------------
@auth.route("/logout")
@login_required
def logout():
    session.pop("token", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
