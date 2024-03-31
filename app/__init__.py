from flask import Flask
import os
import json
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS

app = Flask(__name__, template_folder = r'E:/Spotify/templates')
CORS(app)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Load configuration from settings.json
with open('./settings.json') as config_file:
    config = json.load(config_file)

CLIENT_ID = config['CLIENT_ID']
CLIENT_SECRET = config['CLIENT_SECRET']
REDIRECT_URI = config['REDIRECT_URI']
SCOPE = 'user-read-private user-read-email'

# Spotipy auth manager setup remains the same
auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path='token_info.json')

print("auth manager set up succesful")

## Initialize global cache
from app.utils import initialize_global_cache
from app import routes

initialize_global_cache()