import os
import random
import string
import sys
import urllib.parse
from flask import Flask, redirect, request, session, jsonify, render_template
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import base64
from spotify_smart_playlist_creator.crew import SpotifySmartPlaylistCreator
from threading import Thread



# Configuração da aplicação Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = 'a00b501ab50e412299e0bbbfc695b2c5'
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
CLIENT_SECRET = "0d938d6a4ad24523acc152a64578d0c7"
API_BASE_URL = "https://api.spotify.com/v1"

AUTH_URL = "https://accounts.spotify.com/authorize"

# Função utilitária para gerar estado seguro
def generate_random_string(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Endpoint inicial para login
@app.route('/login')
def login():
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

# Apenas página de boas-vindas opcional
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    saved_state = session.get('state')

    if state is None or state != saved_state:
        return redirect('/?error=state_mismatch')

    # 1. Trocar o code por um access_token ANTES da thread
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
    refresh_token = token_json.get('refresh_token')

    # 2. Preparar inputs fora da thread
    inputs = {
        'user_prompt': 'Crie uma playlist de 5 músicas de axé dos anos 90',
        'access_token': access_token,
        'token': access_token
    }

    def run_agent():
        # Agora a thread usa só os dados locais
        headers = {
            'Authorization': f"Bearer {inputs['access_token']}",
            'Content-Type': 'application/json'
        }

        # Você pode rodar o Crew aqui ou apenas chamar algum endpoint de exemplo
        print("🔍 Inputs enviados ao kickoff:")
        for k, v in inputs.items():
            print(f"  {k}: {str(v)[:60]}")  # Trunca o token por segurança

        print("🔐 Token recebido para o agente:", inputs.get("token", "")[:10], "...")

        result = SpotifySmartPlaylistCreator().crew().kickoff(inputs=inputs)
        print("Agente rodando...")
        print('----------------------------------------')
        print("Resultado do agente:", result)

        
    Thread(target=run_agent).start()

    return render_template('loading.html')

if __name__ == '__main__':
    app.run(port=8888, debug=True)
