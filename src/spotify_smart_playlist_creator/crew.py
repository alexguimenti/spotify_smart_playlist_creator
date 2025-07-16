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
import uuid
import time
import re
import io

from flask import Flask, redirect, request, session, render_template, url_for, jsonify, Response
import requests
import json

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
# In-memory store for agent results and logs (for development only)
# -----------------------------------------------------------------------------

agent_results = {}
agent_logs = {}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def generate_random_string(length=16):
    """Generate a secure random string for state parameter."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def add_log(job_id, message):
    """Add a log message to the agent logs."""
    if job_id not in agent_logs:
        agent_logs[job_id] = []
    agent_logs[job_id].append({
        'timestamp': time.time(),
        'message': message
    })

def parse_crewai_logs(log_text, job_id):
    """Parse CrewAI logs and extract user-friendly progress information."""
    lines = log_text.split('\n')
    songs_list = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and debug info
        if not line or line.startswith('📊') or line.startswith('🚀 Crew: crew'):
            continue
            
        # Extract task completion info
        if 'Task Completed' in line or 'Status: ✅ Completed' in line:
            add_log(job_id, "✅ Task completed successfully")
            
        # Extract agent actions
        elif line.startswith('# Agent:'):
            agent_name = line.replace('# Agent:', '').strip()
            add_log(job_id, f"🤖 {agent_name} is working...")
            
        # Extract tool usage
        elif '## Using tool:' in line:
            tool_name = line.replace('## Using tool:', '').strip()
            add_log(job_id, f"🔧 Using {tool_name}")
            
        # Extract final answers
        elif '## Final Answer:' in line:
            add_log(job_id, "🎯 Finalizing playlist creation...")
            
        # Extract selected songs from AI Music Curator
        elif line.startswith('- "') and ' by ' in line:
            song_info = line.replace('- "', '').replace('"', '')
            songs_list.append(song_info)
            
        # Extract playlist creation success
        elif '"playlist_url"' in line and '"playlist_id"' in line:
            add_log(job_id, "🎵 Playlist created successfully!")
            
        # Extract track addition success
        elif '"status": "Tracks added successfully"' in line:
            add_log(job_id, "🎵 Tracks added to playlist!")
            
        # Extract user info
        elif '"display_name"' in line:
            add_log(job_id, "👤 User profile retrieved")
            
        # Extract track URIs
        elif 'spotify:track:' in line and ',' in line:
            track_count = len(line.split(','))
            add_log(job_id, f" Found {track_count} tracks")
    
    # Show selected songs if any were found
    if songs_list:
        add_log(job_id, " Selected songs:")
        for song in songs_list:
            add_log(job_id, f"   • {song}")

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    """Render the welcome page."""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Receive user prompt and redirect to Spotify login/authorization."""
    user_prompt = request.form.get('user_prompt')
    session['user_prompt'] = user_prompt  # Save it in session for callback
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
    user_prompt = session.get('user_prompt', 'Create a chill evening playlist with 12 acoustic and folk songs.')
    inputs = {
        'user_prompt': user_prompt,
        'access_token': access_token,
        'token': access_token
    }

    # Generate a unique job_id for this agent run
    job_id = str(uuid.uuid4())
    session['job_id'] = job_id
    agent_results[job_id] = None  # Initialize as not ready
    agent_logs[job_id] = []  # Initialize logs

    def run_agent(inputs, job_id):
        """Run the SpotifySmartPlaylistCreator agent in a separate thread."""
        add_log(job_id, "🚀 Agent thread started!")
        add_log(job_id, "🔍 Starting playlist creation process...")
        add_log(job_id, f"📝 User prompt: {inputs['user_prompt']}")
        add_log(job_id, " Token received and validated")
        
        # Set a timeout for the agent execution (5 minutes)
        import signal
        import threading
        
        def timeout_handler():
            add_log(job_id, "⏰ Agent execution timed out after 5 minutes")
            agent_results[job_id] = "timeout"
        
        # Set up timeout
        timer = threading.Timer(300.0, timeout_handler)  # 5 minutes
        timer.start()
        
        # Capture stdout to intercept CrewAI logs
        old_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            add_log(job_id, "🚀 Starting SpotifySmartPlaylistCreator crew...")
            add_log(job_id, "⚙️ Initializing agents and tasks...")
            result = SpotifySmartPlaylistCreator().crew().kickoff(inputs=inputs)
            timer.cancel()  # Cancel timeout if successful
            add_log(job_id, "✅ Agent completed successfully!")
            add_log(job_id, f"🎵 Playlist created: {result}")
        except Exception as e:
            timer.cancel()  # Cancel timeout on error
            add_log(job_id, f"❌ Error during agent execution: {e}")
            import traceback
            traceback.print_exc()
            result = None
        finally:
            # Restore stdout and parse captured logs
            sys.stdout = old_stdout
            captured_logs = captured_output.getvalue()
            parse_crewai_logs(captured_logs, job_id)
        
        # Try to extract playlist URL from result (if possible)
        playlist_url = None
        try:
            add_log(job_id, f"🔍 Extracting playlist URL from result...")
            
            # Handle CrewOutput objects
            if hasattr(result, 'raw'):
                add_log(job_id, "📋 Processing CrewOutput result...")
                result_data = result.raw
                if isinstance(result_data, dict):
                    playlist_url = result_data.get('playlist_url')
                    add_log(job_id, f"✅ Extracted playlist URL: {playlist_url}")
                elif isinstance(result_data, str):
                    # Try to parse as JSON
                    data = json.loads(result_data)
                    playlist_url = data.get('playlist_url')
                    add_log(job_id, f"✅ Extracted playlist URL from JSON: {playlist_url}")
            
            # Handle regular dict
            elif isinstance(result, dict):
                playlist_url = result.get('playlist_url')
                add_log(job_id, f"✅ Extracted playlist URL from dict: {playlist_url}")
            
            # Handle string
            elif isinstance(result, str):
                # Try to parse as JSON
                data = json.loads(result)
                playlist_url = data.get('playlist_url')
                add_log(job_id, f"✅ Extracted playlist URL from string: {playlist_url}")
                
        except Exception as e:
            add_log(job_id, f"❌ Error extracting playlist URL: {e}")
            playlist_url = None
        
        add_log(job_id, f" Final playlist URL: {playlist_url}")
        agent_results[job_id] = playlist_url
        add_log(job_id, "🏁 Process completed!")

    thread = Thread(target=run_agent, args=(inputs, job_id))
    thread.start()
    return redirect(url_for('loading'))

@app.route('/loading')
def loading():
    """Show loading page and poll for agent completion."""
    job_id = session.get('job_id')
    if job_id and agent_results.get(job_id) is not None:
        return redirect(url_for('success'))
    return render_template('loading.html')

@app.route('/status')
def status():
    """Return JSON status if agent is done for polling from loading page."""
    job_id = session.get('job_id')
    done = job_id and agent_results.get(job_id) is not None
    return jsonify({'done': done})

@app.route('/logs')
def logs():
    """Stream logs for the current job using Server-Sent Events."""
    job_id = session.get('job_id')
    print(f"🔍 Logs endpoint called for job_id: {job_id}")
    
    def generate():
        if not job_id:
            print("❌ No job ID found in session")
            yield f"data: {json.dumps({'error': 'No job ID found'})}\n\n"
            return
        
        print(f"📝 Starting log stream for job_id: {job_id}")
        last_log_count = 0
        
        while True:
            if job_id in agent_logs:
                current_logs = agent_logs[job_id]
                print(f" Current logs count: {len(current_logs)}, last sent: {last_log_count}")
                
                if len(current_logs) > last_log_count:
                    # Send new logs
                    for i in range(last_log_count, len(current_logs)):
                        log_entry = current_logs[i]
                        log_data = json.dumps(log_entry)
                        print(f"📤 Sending log: {log_data}")
                        yield f"data: {log_data}\n\n"
                    last_log_count = len(current_logs)
                
                # Check if process is done
                if agent_results.get(job_id) is not None:
                    print(f"✅ Process done for job_id: {job_id}")
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break
            else:
                print(f"⚠️ Job {job_id} not found in agent_logs")
            
            time.sleep(1)  # Wait 1 second before checking again
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/success')
def success():
    """Show success page with playlist link."""
    job_id = session.get('job_id')
    playlist_url = agent_results.get(job_id)
    return render_template('success.html', playlist_url=playlist_url)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(port=8888, debug=True)
