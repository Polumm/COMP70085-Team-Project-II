import asyncio
import random
import time
import requests
import os
import re  # Import regex module
import json
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
)
from werkzeug.security import check_password_hash
from app.routes.auth import (
    decode_jwt,
    login_required,
    generate_jwt,
)  # Import from auth.py
import httpx

chatbot_bp = Blueprint("chatbot_bp", __name__)
# URLs for the other microservices from environment variables
DB_SERVICE_URL = os.getenv("DB_SERVICE_URL")  # Database microservice
CHATBOT_URL = os.getenv("CHATBOT_URL")  # Chatbot microservice


# ----------------------------------------------------
# HOME / LANDING
# ----------------------------------------------------
@chatbot_bp.route("/")
def home():
    """
    Redirect to the multi-session chat if the user is logged in; otherwise, to the login page.
    """
    if session.get("token"):
        return redirect(url_for("chatbot_bp.multisession_chat"))
    return redirect(url_for("auth.login"))


# ----------------------------------------------------
# REGISTRATION
# ----------------------------------------------------
@chatbot_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Show a registration form (GET), or register a new user by calling the DB microservice (POST).
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        if not username or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("chatbot_bp.register"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("chatbot_bp.register"))
        try:
            resp = requests.post(
                f"{DB_SERVICE_URL}/users",
                json={"username": username, "password": password},
                timeout=5,
            )
            if resp.status_code == 201:
                flash(
                    "Registration successful! You can now log in.", "success"
                )
                return redirect(url_for("chatbot_bp.login"))
            else:
                err_data = resp.json()
                flash(err_data.get("error", "Registration failed."), "error")
        except requests.exceptions.RequestException:
            flash("Error contacting user service.", "error")
    return render_template("register.html")


# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
@chatbot_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Show the login form (GET), or authenticate user (POST) by calling DB microservice.
    If successful, store a JWT in Flask session.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Username and password required.")
            return redirect(url_for("chatbot_bp.login"))
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
                    flash("Login successful!")
                    return redirect(url_for("chatbot_bp.multisession_chat"))
                else:
                    flash("Invalid credentials.")
            else:
                flash("User not found.")
        except requests.exceptions.RequestException:
            flash("Error contacting user service.")
    return render_template("login.html")


# ----------------------------------------------------
# LOGOUT
# ----------------------------------------------------
@chatbot_bp.route("/logout")
def logout():
    # If we have a token in session, decode it to find the username
    token = session.get("token")
    if token:
        payload = decode_jwt(token)
        if payload:
            username = payload["username"]
            # Now instruct the DB microservice to sync *all* sessions for that user
            try:
                sync_resp = requests.post(
                    f"{DB_SERVICE_URL}/botchat/logout/{username}", timeout=5
                )
                if sync_resp.status_code != 200:
                    flash(
                        "Warning: Could not fully sync sessions before logout.",
                        "warning",
                    )
            except requests.exceptions.RequestException:
                flash(
                    "DB service is unavailable; could not sync sessions.",
                    "warning",
                )
    # Then remove the JWT from the session to log out
    session.pop("token", None)
    flash("Logged out.")
    return redirect(url_for("chatbot_bp.login"))


# ----------------------------------------------------
# CHAT MANAGEMENT
# ----------------------------------------------------
@chatbot_bp.route("/botchat/sync_session/<session_id>", methods=["POST"])
@login_required
def sync_session(session_id):
    username = g.username
    try:
        requests.post(
            f"{DB_SERVICE_URL}/botchat/sync/{username}/{session_id}", timeout=5
        )
        flash(f"Session '{session_id}' synced to Postgres!", "success")
    except requests.exceptions.RequestException:
        flash("Failed to sync session; DB service unavailable.", "error")
    return redirect(
        url_for("chatbot_bp.multisession_chat", session_id=session_id)
    )


@chatbot_bp.route("/botchat", methods=["GET"])
@login_required
def multisession_chat():
    username = g.username
    # Fetch sessions synchronously using asyncio.run()
    session_ids = asyncio.run(
        _fetch_sessions_concurrently(username, max_attempts=5)
    )
    # Automatically select the first session if none is active
    session_id = request.args.get(
        "session_id", session_ids[0] if session_ids else None
    )
    # Retrieve messages for the active session
    messages = []
    if session_id:
        messages = _fetch_messages_with_retry(
            username, session_id, max_attempts=5
        )
    return render_template(
        "bot_multisession.html",
        session_ids=session_ids,
        active_session_id=session_id,
        messages=messages,
    )


async def _fetch_sessions_concurrently(
    username, num_requests=2, max_attempts=5
):
    """
    Sends `num_requests` concurrent requests to fetch session IDs for a user.
    Implements retry logic with exponential backoff.
    """
    async with httpx.AsyncClient() as client:
        for attempt in range(max_attempts):
            tasks = [
                client.get(
                    f"{DB_SERVICE_URL}/botchat/sessions/{username}", timeout=5
                )
                for _ in range(num_requests)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            session_ids = []
            for resp in responses:
                if (
                    isinstance(resp, httpx.Response)
                    and resp.status_code == 200
                ):
                    session_ids.extend(resp.json().get("sessions", []))
                else:
                    print(f"Attempt {attempt + 1}: Error retrieving sessions.")
            if session_ids:
                return sorted(set(session_ids))  # Return successful result
            # Exponential backoff before retrying
            wait_time = 2**attempt + random.uniform(0, 1)
            print(f"Retrying session fetch in {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
    flash(
        "Database service is unavailable. Some functionality may be limited.",
        "warning",
    )
    return []


def _fetch_sessions_with_retry(username, max_attempts=2):
    """
    Tries to get the session list from the DB microservice up to `max_attempts` times.
    Returns a list of session IDs (or empty list on failure).
    """
    for attempt in range(max_attempts):
        try:
            resp = requests.get(
                f"{DB_SERVICE_URL}/botchat/sessions/{username}", timeout=5
            )
            if resp.status_code == 200:
                print("Debug: Sessions found")
                data = resp.json()
                return sorted(data.get("sessions", []))
            else:
                print("Debug: Sessions not found")
                flash("Error retrieving sessions.", "error")
        except requests.exceptions.RequestException:
            print(
                f"Debug: error from get in _fetch_sessions_with_retry, {attempt = }"
            )
            if attempt == max_attempts - 1:
                flash(
                    "Database service is unavailable. Some functionality may be limited.",
                    "warning",
                )
    return []


def _fetch_messages_with_retry(username, session_id, max_attempts=5):
    """
    Tries to get the messages from the DB microservice up to `max_attempts` times.
    Uses exponential backoff on failures.
    """
    for attempt in range(max_attempts):
        try:
            resp = requests.get(
                f"{DB_SERVICE_URL}/botchat/messages/{username}/{session_id}",
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json().get("messages", [])
            else:
                print(f"Attempt {attempt + 1}: Error retrieving messages.")
        except requests.exceptions.RequestException:
            print(f"Request attempt {attempt + 1} failed.")
        # Exponential backoff
        wait_time = 2**attempt + random.uniform(0, 1)
        print(f"Retrying message fetch in {wait_time:.2f} seconds...")
        time.sleep(wait_time)
    flash("Database service is unavailable. Messages may not load.", "warning")
    return []


@chatbot_bp.route("/botchat/new_session", methods=["POST"])
@login_required
def new_session():
    """
    Create a new chat session while ensuring uniqueness and valid naming per user.
    """
    session_name = request.form["session_name"].strip()
    username = g.username
    if not session_name:
        flash("Session name cannot be empty.", "error")
        return redirect(url_for("chatbot_bp.multisession_chat"))
    # Validate session name (only letters, numbers, spaces, dashes, and underscores)
    if not re.match(r"^[a-zA-Z0-9 _-]+$", session_name):
        flash(
            "Session name contains invalid characters. Use only letters, numbers, spaces, dashes, and underscores.",
            "error",
        )
        return redirect(url_for("chatbot_bp.multisession_chat"))
    # Check if session name already exists for this user (case-insensitive)
    try:
        existing_sessions_resp = requests.get(
            f"{DB_SERVICE_URL}/botchat/sessions/{username}", timeout=5
        )
        if existing_sessions_resp.status_code == 200:
            existing_sessions = existing_sessions_resp.json().get(
                "sessions", []
            )
            existing_sessions_lower = {s.lower() for s in existing_sessions}
            if session_name.lower() in existing_sessions_lower:
                flash(
                    "A session with this name already exists. Please choose a different name.",
                    "error",
                )
                return redirect(url_for("chatbot_bp.multisession_chat"))
    except requests.exceptions.RequestException:
        flash(
            "Database service is unavailable. Cannot check for duplicate session names.",
            "warning",
        )
        return redirect(url_for("chatbot_bp.multisession_chat"))
    # If valid and unique, proceed with creating a new session
    try:
        resp = requests.post(
            f"{DB_SERVICE_URL}/botchat/sessions",
            json={"username": username, "session_name": session_name},
            timeout=5,
        )
        if resp.status_code == 201:
            flash(f"New session '{session_name}' created!", "success")
        else:
            err_data = resp.json()
            flash(err_data.get("error", "Failed to create session."), "error")
            return redirect(url_for("chatbot_bp.multisession_chat"))
    except requests.exceptions.RequestException:
        flash(
            "Database service is unavailable. Session creation failed.",
            "warning",
        )
    return redirect(
        url_for("chatbot_bp.multisession_chat", session_id=session_name)
    )


@chatbot_bp.route("/botchat/select/<session_id>")
@login_required
def select_session(session_id):
    """
    Switch to a different chat session.
    """
    return redirect(
        url_for("chatbot_bp.multisession_chat", session_id=session_id)
    )


@chatbot_bp.route("/botchat/send", methods=["POST"])
@login_required
def send_to_session():
    """
    Send a user message to the chatbot-service, store it in DB microservice,
    then store the bot's response in DB microservice.
    """
    username = g.username
    session_id = request.form.get("session_id", "").strip()
    user_message = request.form.get("message", "").strip()

    if not session_id:
        flash("No session specified.", "error")
        return redirect(url_for("chatbot_bp.multisession_chat"))

    if not user_message:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("chatbot_bp.multisession_chat", session_id=session_id))

    # ✅ Get JWT token from the session and send it in the headers
    token = session.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    print(f"🟡 Debug: Sending request to {CHATBOT_URL}/chat")
    print(f"🟡 Debug: Headers = {headers}")

    # 1️⃣ Store user message in DB
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        user_store_resp = requests.post(
            f"{DB_SERVICE_URL}/botchat/messages",
            json={
                "username": username,
                "sender": "user",
                "session_id": session_id,
                "message": user_message,
                "time": timestamp,
            },
            timeout=5,
        )
        user_store_resp.raise_for_status()
    except requests.exceptions.RequestException:
        flash("Error contacting DB service for user message.", "error")
        return redirect(url_for("chatbot_bp.multisession_chat", session_id=session_id))

    # 2️⃣ Call chatbot-service for a reply (now sending JWT in headers)
    try:
        bot_resp = requests.post(
            f"{CHATBOT_URL}/chat",
            json={"session_id": session_id, "message": user_message},
            headers=headers,  # ✅ Pass token to chatbot-service
            timeout=5,
        )
        if bot_resp.status_code == 200:
            bot_json = bot_resp.json()
            bot_text = json.dumps(bot_json)  # Store the entire JSON response as a string
        else:
            bot_text = json.dumps({"response_type": "text", "response": "Bot did not respond."})
    except requests.exceptions.RequestException:
        bot_text = json.dumps({"response_type": "text", "response": "Error contacting chatbot."})

    # 3️⃣ Store bot's response in DB
    try:
        bot_store_resp = requests.post(
            f"{DB_SERVICE_URL}/botchat/messages",
            json={
                "username": username,
                "sender": "bot",
                "session_id": session_id,
                "message": bot_text,
                "time": (datetime.now() + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"),
            },
            timeout=5,
        )
        bot_store_resp.raise_for_status()
    except requests.exceptions.RequestException:
        flash("Error contacting DB service to store bot response.", "error")

    return redirect(url_for("chatbot_bp.multisession_chat", session_id=session_id))


@chatbot_bp.route("/botchat/delete/<session_id>", methods=["GET"])
@login_required
def delete_session(session_id):
    """
    Delete a chat session by calling the DB microservice,
    then redirect back to the main chat view.
    """
    try:
        # 1) Make a DELETE request to your DB microservice
        resp = requests.delete(
            f"{DB_SERVICE_URL}/botchat/delete/{g.username}/{session_id}",
            timeout=5,
        )
        # 2) Handle response
        if resp.status_code == 200:
            flash(f"Session '{session_id}' deleted.")
        else:
            # Either the session doesn't exist or another error occurred
            error_data = resp.json()
            flash(
                error_data.get("error", "Failed to delete session."), "error"
            )
    except requests.exceptions.RequestException:
        flash("Error contacting DB service.", "error")
    # 3) Redirect back to the main chat page
    return redirect(url_for("chatbot_bp.multisession_chat"))


@chatbot_bp.route("/botchat/search", methods=["GET"])
@login_required
def search_messages():
    """
    Fuzzy search across all chat sessions for the current user.
    Usage: GET /botchat/search?query=xxx
    """
    query = request.args.get("query", "").strip()
    if not query:
        flash("No query provided.", "error")
        return redirect(url_for("chatbot_bp.multisession_chat"))
    username = g.username
    try:
        response = requests.get(
            f"{DB_SERVICE_URL}/botchat/search/{username}",
            params={"query": query},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            return render_template(
                "bot_search.html", results=data.get("results", []), query=query
            )
        else:
            flash("Failed to fetch search results.", "error")
    except requests.exceptions.RequestException:
        flash(
            "Database service is unavailable. Search functionality may be limited.",
            "warning",
        )
    return render_template("bot_search.html", results=[], query=query)
