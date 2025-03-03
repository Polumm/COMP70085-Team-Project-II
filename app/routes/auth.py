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
    jsonify,
)
from app.forms import LoginForm, SignupForm
from functools import wraps
import requests
import os
import jwt
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash

# Blueprint Configuration
auth = Blueprint("auth", __name__)
DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")


# ----------------------------------------------------
# JWT Helpers
# ----------------------------------------------------
def generate_jwt(username, expires_in=3600):
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    secret_key = current_app.config["SECRET_KEY"]
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token):
    try:
        secret_key = current_app.config["SECRET_KEY"]
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def sync_user_sessions(username):
    """
    Instructs the DB microservice to sync all sessions for a user.
    """
    try:
        sync_resp = requests.post(
            f"{DB_SERVICE_URL}/botchat/logout/{username}", timeout=5
        )
        if sync_resp.status_code != 200:
            flash("Warning: Could not fully sync sessions.", "warning")
    except requests.exceptions.RequestException:
        flash("DB service unavailable; could not sync sessions.", "warning")


def login_required(func):
    """Decorator to enforce authentication."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = session.get("token")
        if not token:
            flash("Please log in first.")
            return redirect(url_for("auth.login", next=request.url))

        payload = decode_jwt(token)
        if not payload:
            flash(
                "Session expired. Syncing data and redirecting to login.",
                "warning",
            )
            token = session.pop("token", None)
            if token:
                payload = decode_jwt(token)
                if payload:
                    sync_user_sessions(payload.get("username"))
            return redirect(url_for("auth.login", next=request.url))

        g.username = payload.get("username")
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

        # We'll retry the GET /users/<username> call up to 2 times
        max_attempts = 2
        user_data = None
        service_error = False

        for attempt in range(max_attempts):
            try:
                resp = requests.get(
                    f"{DB_SERVICE_URL}/users/{username}", timeout=5
                )
                if resp.status_code == 200:
                    user_data = resp.json()
                    print("Debug: User found")
                else:
                    # e.g. 404 => "User not found"
                    flash("User not found.", "danger")
                    print("Debug: User not found")
                # Break out of the for-loop if we got a valid response (200 or 404)
                break
            except requests.exceptions.RequestException:
                print(f"Debug: error from get in login, {attempt = }")
                # If it's the last attempt, set service_error => True
                if attempt == max_attempts - 1:
                    service_error = True

        # If both attempts failed with a RequestException:
        if service_error:
            print("Debug: service_error")
            flash("Error contacting user service.", "danger")
            return render_template("login.html", form=form)

        # If user_data is None, it means we got a non-200 response (404 or something else)
        # But we already flashed "User not found." or "Error contacting user service."
        # so just re-render the form:
        if not user_data:
            print("Debug: user_data is None")
            return render_template("login.html", form=form)

        # Otherwise, check password:
        if check_password_hash(user_data["password_hash"], password):
            token = generate_jwt(username)
            session["token"] = token
            session["user_id"] = user_data["id"]  # ✅ Store user_id in session
            session["username"] = username # Store username in session
            flash("Login successful!", "success")
            return redirect(next_page or url_for("main.home"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login.html", form=form)


# ----------------------------------------------------
# Logout Route
# ----------------------------------------------------
@auth.route("/logout")
@login_required
def logout():
    username = g.username
    sync_user_sessions(username)  # Sync all sessions before logout
    session.pop("token", None)
    session.pop("user_id", None)  # ✅ Remove user_id from session
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.home"))


# ----------------------------------------------------
# Heartbeat Route
# ----------------------------------------------------
@auth.route("/heartbeat", methods=["POST"])
@login_required
def heartbeat():
    """
    Update last-seen time for the user's session in the DB microservice.
    """
    username = g.username
    token = session.get("token")
    if token:
        payload = decode_jwt(token)
        if payload:
            try:
                requests.post(
                    f"{DB_SERVICE_URL}/botchat/update_session_expiry",
                    json={"username": username, "exp": payload["exp"]},
                    timeout=5,
                )
            except requests.exceptions.RequestException:
                flash(
                    "Error contacting DB service to update session expiry.",
                    "warning",
                )
    return jsonify({"status": "ok"})


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
