from flask import Flask, request, redirect, session, url_for, render_template, jsonify
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import uuid
from werkzeug.exceptions import HTTPException
import logging
import json 

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Spotify OAuth settings using values from the configuration file
# Load configuration from settings.json
with open('settings.json') as config_file:
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

@app.before_request
def ensure_session_uuid():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
        logging.info("New UUID created for session")

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/')
def home():
    ensure_session_uuid()
    logging.info("home page")

    token_info = auth_manager.get_cached_token()
    if token_info:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return render_template('home.html')
    else:
        return redirect(url_for('signin'))
    
@app.route('/login')
def login():
    ensure_session_uuid()
    if not auth_manager.get_cached_token():
        auth_url = auth_manager.get_authorize_url(state=session['uuid'])
        return redirect(auth_url)
    return redirect(url_for('home'))

@app.route('/callback')
def callback():
    session['uuid'] = str(uuid.uuid4())  # Refresh the session UUID
    code = request.args.get('code')

    # This line might automatically handle token caching and refreshing internally.
    auth_manager.get_access_token(code)

    # Use get_cached_token() if you need to access the token information as a dictionary.
    token_info = auth_manager.get_cached_token()

    if not token_info:
        try:
            auth_manager.get_access_token(code)
            logging.info("Access token fetched successfully")
        except Exception as e:
            logging.error(f"Error fetching access token: {e}")
            return redirect(url_for('error'))


    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logging.info("Logging out, clearing session and token cache.")
    try:
        # Attempt to remove the token cache file to ensure user data is destroyed
        os.remove('token_info.json')
    except FileNotFoundError:
        logging.warning("Token info file not found during logout.")
    
    # Clear the Flask session
    session.clear()
    logging.info("Session cleared.")

    # Redirect the user to the sign-in page
    return redirect(url_for('signin'))


@app.route('/get-playlists')
def get_playlists():
    # Ensure authentication and user session exist
    if not auth_manager.get_cached_token():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        playlists_data = get_user_playlists_with_tracks(sp)
        return jsonify(playlists_data)
    except Exception as e:
        logging.error(f"Error fetching playlists: {e}")
        return jsonify({'error': 'Failed to fetch playlists'}), 500
    
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # For non-HTTP exceptions, return a generic error message
    logging.error(f"Unhandled exception: {e}")
    return render_template("error.html", error=str(e)), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    # More detailed logging for debugging
    logging.error(f"HTTP Exception: {e} | Description: {e.descri5ption}, Status Code: {e.code}")
    
    # Render an error template with more context
    return render_template("http_error.html", 
                           error=e.description, 
                           code=e.code,
                           suggestion="Please check the URL or try again later."), e.code


def get_user_playlists_with_tracks(sp):
    playlists_data = []
    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists['items']:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        playlist_tracks = []
        
        # Fetch tracks for this playlist
        tracks_response = sp.playlist_tracks(playlist_id, limit=100)
        while tracks_response:
            for item in tracks_response['items']:
                track = item['track']
                track_info = {
                    'name': track['name'],
                    'artist': ', '.join(artist['name'] for artist in track['artists']),
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'spotify_url': track['external_urls']['spotify']
                }
                playlist_tracks.append(track_info)
            
            # Check for more tracks
            if tracks_response['next']:
                tracks_response = sp.next(tracks_response)
            else:
                tracks_response = None

        playlists_data.append({
            'id': playlist_id,
            'name': playlist_name,
            'tracks': playlist_tracks
        })
    
    return playlists_data

if __name__ == '__main__':
    app.run(debug=True)
