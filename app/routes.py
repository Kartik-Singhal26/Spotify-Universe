from flask import request, redirect, session, url_for, render_template, jsonify
from app import app, auth_manager, utils
import spotipy
import uuid
import logging
from werkzeug.exceptions import HTTPException
import os
import json
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Setup base directory and paths
basedir = os.path.abspath(os.path.dirname(__file__))
project_basedir = os.path.join(basedir, os.pardir)
token_info_path = os.path.join(project_basedir, 'token_info.json')
json_file_path = os.path.join(project_basedir, 'user_data.json')

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
    logging.info("Accessing home page.")
    token_info = auth_manager.get_cached_token()
    if token_info:
        logging.info("Token found, rendering home page.")
        user_details_response, response_code_user_details = get_user_account_details()  
        user_stats_response, response_code_user_stats = get_user_stats()  

        if response_code_user_details == 200 and response_code_user_stats == 200:
            user_details = user_details_response.get_json()  # Extract JSON data from the response
            user_stats = user_stats_response.get_json()  # Extract JSON data from the response
            return render_template('index.html', user_info=user_details, user_stats=user_stats)
        else:
            logging.error("Failed to fetch user details or stats.")
            return redirect(url_for('error'))  # Redirect to an error handling route
    else:
        logging.info("No token found, redirecting to login page.")
        return redirect(url_for('signin'))

@app.route('/content/<page>')
def content(page):
    if page == 'playlists':
        # Directly return the rendered HTML template for playlists
        return render_template('partials/_playlists.html')
    # Handle other pages or return a 404/error if the page does not exist
    return render_template('error.html')


@app.route('/login')
def login():
    """Handles the login process by checking for a cached token or redirecting to Spotify for authentication."""
    logging.info("Attempting login.")
    if not auth_manager.get_cached_token():
        auth_url = auth_manager.get_authorize_url(state=session['uuid'])
        logging.info(
            "No cached token, redirecting to Spotify for authentication.")
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

@app.route('/get-user-details/', methods=['GET'])
def get_user_account_details():
    """
    Endpoint to get Spotify user details.
    """
    try:
        # Call the current_user() method to fetch the user's details
        user_info = sp.current_user()
        
        # Assuming you want to return some basic information about the user
        user_details = {
            'display_name': user_info.get('display_name'),
            'email': user_info.get('email'),
            'id': user_info.get('id'),
            'country': user_info.get('country'),
            'followers': user_info.get('followers', {}).get('total', 0)
        }

        logging.info("Successfully fetched user details.")
        return jsonify(user_details), 200

    except Exception as e:
        logging.error(f"Failed to fetch user details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-user-stats/', methods=['GET'])
def get_user_stats():
    """
    Route to fetch and return user statistics.
    """
    stats = utils.calculate_user_stats()
    if stats is None:
        # Handling the case where stats calculation fails
        return jsonify({'error': 'Unable to calculate user stats'}), 500
    
    # If calculation is successful, return the stats
    return jsonify(stats), 200

@app.route('/get-all-playlists')
def get_all_playlist_data():
    """
    Endpoint to retrieve the current user's playlists data from the cache.
    If cache is empty or outdated, fetches from Spotify and updates the cache.
    """
    try:
        ## Refresh Cache 
        utils.ensure_cache_data_freshness(sp)

        # Attempt to retrieve playlist data from the cache first
        playlists_data = utils.get_all_playlist_data_from_cache()

        # If the cache was empty or outdated, fetch from Spotify and update the cache
        if not playlists_data:
            logging.info("Cache is empty or outdated, fetching playlists data from Spotify.")

        if playlists_data:
            logging.info("Playlists data retrieved successfully.")
            return jsonify(playlists_data)
        else:
            logging.error("Playlists data is empty after attempting to fetch and cache.")
            return jsonify({'error': 'Failed to fetch playlists - Data is empty after update'}), 500
    except Exception as e:
        logging.error(f"Failed to fetch playlists: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-playlist/<playlist_id>')
def get_playlist_by_id(playlist_id):
    """
    Endpoint to retrieve data for a specific playlist by its ID.
    If the playlist data is not in the cache or is outdated, fetches from Spotify and updates the cache.
    """
    try:
        # Attempt to retrieve specific playlist data from the cache first
        playlist_data = utils.get_playlist_data_by_id_from_cache(playlist_id)

        # If the cache was empty or outdated, fetch from Spotify and update the cache
        if not playlist_data:
            logging.info(f"Cache is empty or outdated for playlist ID {playlist_id}, fetching data from Spotify.")
            utils.ensure_cache_data_freshness(sp)

            # After fetching and caching, retrieve the updated data from the cache
            playlist_data = utils.get_playlist_data_by_id_from_cache(playlist_id)

        if playlist_data:
            logging.info(f"Playlist data for ID {playlist_id} retrieved successfully.")
            return jsonify(playlist_data)
        else:
            logging.error(f"Playlist data is empty for ID {playlist_id} after attempting to fetch and cache.")
            return jsonify({'error': f'Failed to fetch playlist for ID {playlist_id} - Data is empty after update'}), 500
    except Exception as e:
        logging.error(f"Failed to fetch playlist for ID {playlist_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/playlist-metrics/<playlist_id>', methods=['GET'])
def playlist_metrics(playlist_id):
    """
    Endpoint to retrieve metrics for a specific playlist by its ID.
    """
    try:
        metrics = utils.get_playlist_metric_by_id(playlist_id)
        if metrics:
            logging.info(f"Metrics for playlist ID {playlist_id} retrieved successfully.")
            return jsonify(metrics)
        else:
            return jsonify({'error': f'Failed to calculate metrics for playlist ID {playlist_id}'}), 500
    except Exception as e:
        logging.error(f"Failed to fetch metrics for playlist {playlist_id}: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/get-all-tracks-for-playlist/<playlist_id>', methods=['GET'])
def get_all_tracks_for_palylist(playlist_id):
    """
    Fetches tracks from the specified playlist by its ID, utilizing cache.
    """
    try:
        # Attempt to get tracks data from the cache
        simplified_tracks = utils.get_playlist_wise_tracks_information_from_cache(playlist_id)
        
        # If cache miss, refresh cache data and attempt to fetch again
        if simplified_tracks is None:
            logging.info(f"Cache miss for playlist ID {playlist_id}. Refreshing cache.")
            return jsonify({'error': 'Failed to fetch tracks for the playlist'}), 500

        # Successfully retrieved data
        logging.info(f"Tracks for playlist ID {playlist_id} retrieved successfully.")
        return jsonify(simplified_tracks)
    except Exception as e:
        logging.error(f"Failed to fetch tracks for playlist {playlist_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-all-tracks-for_user')
def get_all_tracks_data():
    """
    Endpoint to retrieve the current user's tracks data from the cache.
    If cache is empty or outdated, fetches from Spotify and updates the cache.
    """
    try:
        # Attempt to retrieve playlist data from the cache first
        tracks_data = utils.get_all_tracks_data_from_cache()

        # If the cache was empty or outdated, fetch from Spotify and update the cache
        if not tracks_data:
            logging.info("Cache is empty or outdated, fetching Tracks data from Spotify.")
            tracks_data = utils.ensure_cache_data_freshness(sp, auth_manager, json_file_path)

            # After fetching and caching, retrieve the updated data from the cache
            tracks_data = utils.get_all_tracks_data_from_cache()

        if tracks_data:
            logging.info("Tracks data retrieved successfully.")
            return jsonify(tracks_data)
        else:
            logging.error("Tracks data is empty after attempting to fetch and cache.")
            return jsonify({'error': 'Failed to fetch Tracks - Data is empty after update'}), 500
    except Exception as e:
        logging.error(f"Failed to fetch Tracks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-track/<track_id>', methods=['GET'])
def get_track_by_id(track_id):
    """
    Fetches details for a specific track by its Spotify ID, utilizing cache. if not found in cache, searches spotify
    """
    try:
        # Attempt to get track data from the cache
        track_info = utils.get_track_information_from_cache(track_id)

        # If cache miss, refresh cache data and attempt to fetch again
        if track_info is None:
            logging.info(f"Cache miss for track ID {track_id}. Checking Spotify.")
            track_info = utils.fetch_track_by_id_from_spotify(track_id)

            if track_info is None:
                logging.error(f"Unable to retrieve track for ID {track_id} from spotify.")
                return jsonify({'error': f'Failed to fetch track for ID {track_id}'}), 500

        logging.info(f"Track for ID {track_id} retrieved successfully.")
        return jsonify(track_info)
    except Exception as e:
        logging.error(f"Failed to fetch track for ID {track_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/refresh_token')
def refresh_token():
    try:
        token_info = auth_manager.refresh_access_token(
            session.get('token_info').get('refresh_token'))
        session['token_info'] = token_info  # Update session with new token
        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Error refreshing token: {e}")
        return jsonify(success=False), 401

@app.before_request
def make_session_permanent():
    session.permanent = True  # Make the user session persistent
    app.permanent_session_lifetime = timedelta(
        minutes=60)  # Adjust as necessary

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
