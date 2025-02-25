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
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash

# Blueprint Configuration
auth = Blueprint("auth", __name__)


# ----------------------------------------------------
# JWT Helpers
# ----------------------------------------------------
def generate_jwt(username, expires_in=3600):
    """
    Generate a JWT that expires in 'expires_in' seconds.
    """
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    secret_key = current_app.config["SECRET_KEY"]  # Get from Flask config
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token):
    """
    Decode a JWT, returning its payload or None if invalid/expired.
    """
    try:
        secret_key = current_app.config["SECRET_KEY"]
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(func):
    """
    Custom decorator to ensure a user is logged in.
    If not, redirect to the login page with 'next' parameter.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = session.get("token")
        if not token:
            flash("Please log in first.")
            # Preserve the next page the user was trying to access
            return redirect(url_for("auth.login", next=request.url))

        payload = decode_jwt(token)
        if not payload:
            flash("Session expired. Please log in again.")
            session.pop("token", None)
            return redirect(url_for("auth.login", next=request.url))

        # Store username in flask.g for downstream routes
        g.username = payload["username"]
        return func(*args, **kwargs)

    return wrapper


# ----------------------------------------------------
# Login Route
# ----------------------------------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Display the login form and authenticate the user.
    Redirect to the originally requested page after login
    or go to the multi-session chat if none specified.
    """
    form = LoginForm()
    next_page = request.args.get("next")  # Capture 'next' parameter

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Call DB microservice to authenticate user
        try:
            resp = requests.get(
                f"{current_app.config['DB_SERVICE_URL']}/users/{username}",
                timeout=5,
            )
            if resp.status_code == 200:
                user_data = resp.json()
                if check_password_hash(user_data["password_hash"], password):
                    # Generate JWT and store in session
                    token = generate_jwt(username)
                    session["token"] = token
                    flash("Login successful!", "success")

                    # Redirect to the originally requested page,
                    # or go to the multi-session chat by default
                    return redirect(
                        next_page or url_for("chatbot_bp.multisession_chat")
                    )
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
    """
    Display the signup form and register a new user.
    """
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
                f"{current_app.config['DB_SERVICE_URL']}/users",
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
    """
    Logout the user by clearing the JWT token from session.
    """
    session.pop("token", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
