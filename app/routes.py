from flask import request, redirect, session, url_for, render_template, jsonify
from app import app, auth_manager
from app.utils import fetch_and_cache_playlists, calculate_user_stats
import spotipy
import uuid
import logging
from werkzeug.exceptions import HTTPException
import os
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup base directory and paths
basedir = os.path.abspath(os.path.dirname(__file__))
project_basedir = os.path.join(basedir, os.pardir)
token_info_path = os.path.join(project_basedir, 'token_info.json')
json_file_path = os.path.join(project_basedir, 'playlists_data.json')

sp = spotipy.Spotify(auth_manager=auth_manager)

@app.before_request
def ensure_session_uuid():
    """Ensures that each session has a unique UUID. If not present, a new UUID is created and assigned."""
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
        logging.info("Session UUID created: %s", session['uuid'])

@app.route('/signin')
def signin():
    """Renders the sign-in page."""
    logging.info("Rendering signin page.")
    return render_template("signin.html")

@app.route('/')
def home():
    """Handles the route to the home page. Fetches token and user information to render the home page or redirects to sign-in if no token is found."""
    logging.info("Accessing home page.")
    token_info = auth_manager.get_cached_token()
    if token_info:
        logging.info("Token found, rendering home page.")
        user_info = sp.current_user()
        user_stats = calculate_user_stats(sp)
        return render_template('home.html', user_info=user_info, user_stats=user_stats)
    else:
        logging.info("No token found, redirecting to login page.")
        return redirect(url_for('signin'))

@app.route('/login')
def login():
    """Handles the login process by checking for a cached token or redirecting to Spotify for authentication."""
    logging.info("Attempting login.")
    if not auth_manager.get_cached_token():
        auth_url = auth_manager.get_authorize_url(state=session['uuid'])
        logging.info("No cached token, redirecting to Spotify for authentication.")
        return redirect(auth_url)
    logging.info("Token already cached, redirecting to home.")
    return redirect(url_for('home'))

@app.route('/callback')
def callback():
    """Handles the callback from Spotify authentication, retrieving and caching the access token."""
    logging.info("Received callback from Spotify.")
    session['uuid'] = str(uuid.uuid4())
    code = request.args.get('code')
    logging.info("Authorization code received: %s", code)
    auth_manager.get_access_token(code)
    logging.info("Access token retrieved and cached successfully.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Logs out the user by clearing the session and removing the token info file."""
    logging.info("Logging out user.")
    try:
        # Clear token info from session
        if 'token_info' in session:
            session.pop('token_info', None)
            logging.info("Token info cleared from session.")
            
        # Remove the token info file
        if os.path.exists(token_info_path):
            os.remove(token_info_path)
            logging.info("Token info file successfully removed.")
    except Exception as e:
        logging.error(f"Error during logout: {e}")
    
    # Clear the entire session
    session.clear()
    logging.info("Session cleared.")

    # Redirect the user to the sign-in page
    return redirect(url_for('signin'))

@app.route('/get-playlist-details/<playlist_id>', methods=['GET'])
def get_playlist_details(playlist_id):
    """Fetches details for a specific playlist given its ID. Returns a JSON object with playlist details."""
    try:
        playlist = sp.playlist(playlist_id)
        playlist_details = {
            'name': playlist['name'],
            'description': playlist['description'],
            'owner': playlist['owner']['display_name'],
            'total_tracks': playlist['tracks']['total']
        }
        return jsonify(playlist_details)
    except Exception as e:
        logging.error(f"Failed to fetch playlist details: {e}")
        return jsonify({'error': str(e)}), 404

@app.route('/get-playlists')
def get_playlist_data():
    """Endpoint to retrieve the current user's playlists data."""
    try:
        playlists_data = fetch_and_cache_playlists(sp, auth_manager, json_file_path)
        if playlists_data:
            return jsonify(playlists_data)
        else:
            logging.error("Playlists data is empty.")
            return jsonify({'error': 'Failed to fetch playlists - Data is empty'}), 500
    except Exception as e:
        logging.error(f"Failed to fetch playlists: {e}")
        return jsonify({'error': 'Failed to fetch playlists'}), 500

@app.route('/get-tracks/<playlist_id>', methods=['GET'])
def get_tracks(playlist_id):
    """Fetches tracks from the specified playlist by its ID.

    Args:
        playlist_id (str): The ID of the playlist to fetch tracks from.

    Returns:
        flask.Response: A JSON response containing the fetched tracks.

    Raises:
        Exception: If there is an error while fetching the tracks.
    """
    try:
        results = sp.playlist_tracks(playlist_id)
        simplified_tracks = []
        for item in results['items']:
            track = item.get('track')
            if track and track.get('duration_ms', 0) != 0:
                images = track.get('album', {}).get('images', [])
                image_url = images[0].get('url', 'default_image_url') if images else 'default_image_url'
                
                simplified_track = {
                    'name': track.get('name', ''),
                    'artist': ', '.join(artist['name'] for artist in track.get('artists', [])),
                    'album': track.get('album', {}).get('name', ''),
                    'duration_ms': track.get('duration_ms', 0),
                    'spotify_url': track.get('external_urls', {}).get('spotify', ''),
                    'image_url': image_url
                }
                simplified_tracks.append(simplified_track)
        return jsonify(simplified_tracks)
    except Exception as e:
        logging.error(f"Failed to fetch tracks for playlist {playlist_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/refresh_token')
def refresh_token():
    try:
        token_info = auth_manager.refresh_access_token(session.get('token_info').get('refresh_token'))
        session['token_info'] = token_info  # Update session with new token
        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Error refreshing token: {e}")
        return jsonify(success=False), 401

@app.before_request
def make_session_permanent():
    session.permanent = True  # Make the user session persistent
    app.permanent_session_lifetime = timedelta(minutes=60)  # Adjust as necessary


@app.errorhandler(Exception)
def handle_exception(e):
    """Catches unhandled exceptions and logs them, returning a generic error page."""
    logging.error("Unhandled exception: %s", e)
    return render_template("error.html", error=str(e)), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handles HTTP exceptions by logging and displaying an error page with relevant information."""
    logging.error("HTTP Exception: %s, Status Code: %d", e.description, e.code)
    return render_template("error.html", error=e.description, code=e.code, suggestion="Please check the URL or try again later."), e.code
