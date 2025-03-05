import hashlib
import time
import random
import uuid
from locust import HttpUser, task, between

# Pool of mock usernames that already exist in your DB
USER_POOL = [f"mock-{i}" for i in range(1, 1001)]
DEFAULT_PASSWORD = "password"  # assuming a default password for tests

def generate_global_hash(username):
    """
    Generates a pseudo-unique hash using the username, current time, and a UUID.
    Truncates the SHA-256 hash to 16 characters for readability.
    """
    unique_string = f"{username}-{time.time()}-{uuid.uuid4()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

class ChatMessageUser(HttpUser):
    # Wait randomly between 0.5s and 1.0s after each task
    wait_time = between(0.5, 1.0)

    def on_start(self):
        """
        When a Locust user spawns:
          1. Pick a username and simulate a login via the /auth/login endpoint.
          2. Generate a unique session name.
          3. Create a new session via the /botchat/new_session endpoint.
        """
        # Choose a username and set the default password
        self.username = random.choice(USER_POOL)
        self.password = DEFAULT_PASSWORD

        # 1. Simulate login using the client's /auth/login endpoint
        login_resp = self.client.post(
            "/auth/login",
            data={"username": self.username, "password": self.password},
            name="login",
        )
        if login_resp.status_code not in (200, 302):  # 302 may be a redirect on successful login
            print(f"❌ Failed to login for user {self.username}: {login_resp.text}")
        else:
            # Explicitly update the session cookies if needed
            self.client.cookies.update(login_resp.cookies)
            print(f"✅ Login successful for user {self.username}")

        # 2. Generate a unique session name
        self.session_name = f"test_session_{generate_global_hash(self.username)}".lower()

        # 3. Create a new session via the /botchat/new_session endpoint (expects form data)
        create_resp = self.client.post(
            "/chatbot/botchat/new_session",
            data={"session_name": self.session_name},
            name="create_session",
        )
        if create_resp.status_code not in (200, 201, 302):
            print(f"❌ Failed to create session: {create_resp.text}")
        else:
            print(f"✅ Session created: {self.session_name}")

    @task(1)
    def get_sessions_list(self):
        """
        Retrieve the multi-session chat page.
        This endpoint is now at `/botchat` and returns HTML.
        """
        get_resp = self.client.get(
            "/chatbot/botchat",
            name="get_sessions"
        )
        if get_resp.status_code == 200:
            print(f"✅ Fetched multi-session chat page for user {self.username}")
        else:
            print(f"❌ Failed to fetch multi-session chat page: {get_resp.text}")

    @task(3)
    def send_messages(self):
        """
        Send a message using the /botchat/send endpoint.
        """
        # The /botchat/send endpoint expects form data along with a conversation state.
        message_payload = {
            "session_id": self.session_name,
            "message": f"Hello from locust user {self.username}",
            "conversation_state": "{}",
        }
        message_resp = self.client.post(
            "/chatbot/botchat/send",
            data=message_payload,
            name="send_message"
        )
        if message_resp.status_code in (200, 201, 302):
            print(f"✅ Message sent for session {self.session_name}")
        else:
            print(f"❌ Failed to send message: {message_resp.text}")

