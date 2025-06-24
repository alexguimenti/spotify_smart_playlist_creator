"""
Flask app for Spotify Smart Playlist Creator
"""

import os
import sys
import random
import string
import urllib.parse
import base64
from threading import Thread

from flask import Flask, redirect, request, session, render_template
import requests

# Optionally load environment variables from a .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

# Local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from spotify_smart_playlist_creator.crew import SpotifySmartPlaylistCreator

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
API_BASE_URL = "https://api.spotify.com/v1"
AUTH_URL = "https://accounts.spotify.com/authorize"

app = Flask(__name__)
app.secret_key = os.urandom(24)

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def generate_random_string(length=16):
    """Generate a secure random string for state parameter."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    """Render the welcome page."""
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect user to Spotify login/authorization."""
    state = generate_random_string(16)
    session['state'] = state
    scope = 'user-read-private user-read-email playlist-modify-private playlist-modify-public'
    query_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'state': state,
        'show_dialog': 'true'
    }
    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(query_params)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle Spotify callback, exchange code for token, and start agent thread."""
    code = request.args.get('code')
    state = request.args.get('state')
    saved_state = session.get('state')
    if state is None or state != saved_state:
        return redirect('/?error=state_mismatch')

    # Exchange code for access token
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    token_headers = {
        'Authorization': f"Basic {auth_header}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post('https://accounts.spotify.com/api/token', data=token_data, headers=token_headers)
    if response.status_code != 200:
        return f"Token request failed: {response.text}"
    token_json = response.json()
    access_token = token_json['access_token']

    # Prepare agent inputs
    inputs = {
        'user_prompt': 'Create a playlist with 5 punk rock songs from the 90s and 2000s with bands like Blink and Green Day',
        'access_token': access_token,
        'token': access_token
    }

    def run_agent(inputs):
        """Run the SpotifySmartPlaylistCreator agent in a separate thread."""
        print("🔍 Inputs sent to kickoff:")
        for k, v in inputs.items():
            print(f"  {k}: {str(v)[:60]}")  # Truncate token for security
        print("🔐 Token received for agent:", inputs.get("token", "")[:10], "...")
        result = SpotifySmartPlaylistCreator().crew().kickoff(inputs=inputs)
        print("Agent running...")
        print('----------------------------------------')
        print("Agent result:", result)

    Thread(target=run_agent, args=(inputs,)).start()
    return render_template('loading.html')

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(port=8888, debug=True)
