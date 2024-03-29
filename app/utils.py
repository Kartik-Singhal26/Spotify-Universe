import logging
import os
from spotipy import Spotify
from app import auth_manager
import numpy as np
from models import SpotifyCache

## Follow the followinmg sequence : define -> update(indiv) -> update(bulk) -> get (indiv) -> get(bulk) while  organizing functions 

# You might need to adjust these paths based on your project structure and how you manage configuration
basedir = os.path.abspath(os.path.dirname(__file__))
project_basedir = os.path.join(basedir, os.pardir)
json_file_path = os.path.join(project_basedir, 'user_data.json')

# Initialize the global cache object
global spotify_cache
spotify_cache = None

##----------------- Application Specific -------------------##
def is_current_token_valid():
    """
    Checks if the current Spotify authentication token is valid.

    Returns:
    bool: True if the token is valid, False otherwise.
    """
    if not auth_manager.validate_token(auth_manager.get_cached_token()):
        logging.warning("Spotify user not authenticated.")
        return False
    return True

def initialize_global_cache():
    global spotify_cache  # Access the global cache object
    if is_current_token_valid():
        spotify_cache = SpotifyCache(json_file_path=json_file_path)
        logging.info("Global Spotify cache initialized.")
    else:
        logging.error(
            "Failed to initialize global Spotify cache due to authentication issues.")

def get_spotify_cache_instance():
    """
    Returns the global instance of the SpotifyCache.

    This function provides access to the cached Spotify data, including playlists, tracks, and artists.

    Returns:
    SpotifyCache: The global SpotifyCache instance.
    """
    global spotify_cache
    if spotify_cache is not None:
        return spotify_cache
    else:
        logging.error("Spotify cache is not initialized.")
        return None

##----------------- User Data Specific -------------------##

def fetch_user_playlists_with_tracks_from_spotify(sp: Spotify):
    """
    Fetches playlists and their tracks for the current user from Spotify,
    and organizes the data into three structures: playlists, tracks, and artists.

    Args:
    - sp: An authenticated spotipy.Spotify client.

    Returns:
    A tuple containing three dictionaries:
    - The first dictionary lists playlists with their track IDs.
    - The second dictionary contains details for all unique tracks.
    - The third dictionary contains details for all unique artists.
    """
    playlists_data = []
    tracks_details = {}
    artists_details = {}

    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists['items']:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        playlist_images = playlist['images']
        playlist_image_url = playlist_images[0]['url'] if playlist_images else None

        playlist_track_ids = []
        tracks_response = sp.playlist_tracks(playlist_id, limit=100)
        while tracks_response:
            for item in tracks_response['items']:
                track = item['track']
                if track is not None:
                    track_id = track['id']
                    playlist_track_ids.append(track_id)

                    # Populate track details if not already done
                    if track_id not in tracks_details:
                        track_album_images = track['album']['images']
                        track_image_url = track_album_images[0]['url'] if track_album_images else None
                        tracks_details[track_id] = {
                            'name': track['name'],
                            # Store artist IDs
                            'artists': [artist['id'] for artist in track['artists']],
                            'album': track['album']['name'],
                            'duration_ms': track['duration_ms'],
                            'spotify_url': track['external_urls']['spotify'],
                            'image_url': track_image_url
                        }

                        # Populate artist details if not already done
                        for artist in track['artists']:
                            artist_id = artist['id']
                            if artist_id not in artists_details:
                                artists_details[artist_id] = {
                                    'name': artist['name'],
                                    'spotify_url': artist['external_urls']['spotify'],
                                    'genre': artist['genres'],
                                    'popularity': artist['popularity']
                                }

            if tracks_response['next']:
                tracks_response = sp.next(tracks_response)
            else:
                tracks_response = None

        playlists_data.append({
            'id': playlist_id,
            'name': playlist_name,
            'image_url': playlist_image_url,
            'track_ids': playlist_track_ids  # Store only track IDs
        })

    return playlists_data, tracks_details, artists_details

def ensure_cache_data_freshness(sp: Spotify):
    """
    Checks the cache for validity and freshness. Fetches and caches the playlist data, track details, and artist details
    if the cache is not valid or is missing data. This function can be reused across different parts of an application.

    Args:
    - sp: An authenticated spotipy.Spotify client.

    Returns:
    A tuple containing three elements: playlist data, track details, and artist details.
    Uses cached data if it is considered valid, otherwise fetches from Spotify.
    """
    logging.info(
        "Checking cache status for playlists, tracks, and artists data.")

    if not is_current_token_valid():
        logging.warning("Spotify user not authenticated.")
        return None, None, None

    # Attempt to load from cache first
    global spotify_cache

    if spotify_cache.is_cache_valid():
        logging.info("Cache is valid. Using cached data.")
    else:
        logging.info("Cache is outdated or incomplete. Fetching new data...")
        try:
            # Fetch new data from Spotify
            playlists_data, tracks_details, artists_details = fetch_user_playlists_with_tracks_from_spotify(
                sp)
            # Update the cache with the new data
            spotify_cache.update_cache(
                playlists_data, tracks_details, artists_details)
            logging.info("Data successfully fetched and cached.")
        except Exception as e:
            logging.error(f"Error while fetching or caching data: {e}")
            return None, None, None

def calculate_user_stats():
    """
    Calculates and returns user statistics based on their playlists, tracks, and artists data from the cache.
    """
    spotify_cache = get_spotify_cache_instance()
    if not spotify_cache:
        logging.error("Spotify cache instance is not available.")
        return None

    playlists_data = spotify_cache.playlist_cache
    tracks_details = spotify_cache.tracks_cache
    artists_details = spotify_cache.artists_cache

    # Check if data is present
    if not playlists_data or not tracks_details or not artists_details:
        logging.info("Cache data is missing. Statistics cannot be calculated.")
        return {
            'num_playlists': 0,
            'num_unique_tracks': 0,
            'num_unique_artists': 0
        }

    num_playlists = len(playlists_data)
    # Using keys directly as they represent unique track IDs
    unique_tracks = set(tracks_details)
    # Using keys directly as they represent unique artist IDs
    unique_artists = set(artists_details)

    return {
        'num_playlists': num_playlists,
        'num_unique_tracks': len(unique_tracks),
        'num_unique_artists': len(unique_artists)
    }

##----------------- Track Specific -------------------##

def fetch_track_by_id_from_spotify(sp: Spotify, track_id):
    """
    Fetches a track by its ID directly from Spotify if not available in the cache.
    Updates the cache with the fetched track data.

    Args:
    - track_id: The Spotify ID of the track.

    Returns:
    - A dictionary representing the fetched track if successful, None otherwise.
    """
    try:
        # Attempt to retrieve the track data from the cache first
        track_info = get_track_information_from_cache(track_id)

        if track_info:
            logging.info("Track found in cache.")
            return track_info
        else:
            # If not in cache, fetch from Spotify
            logging.info("Track not found in cache. Fetching from Spotify.")
            fetched_track = sp.track(track_id)  # Fetch the track using Spotipy

            if fetched_track:
                return fetched_track
            else:
                logging.warning(
                    f"No data returned for track ID {track_id} from Spotify.")
                return None
    except Exception as e:
        logging.error(f"Failed to fetch track ID {track_id} from Spotify: {e}")
        return None

def get_track_information_from_cache(track_id):
    """
    Retrieves detailed information for a specific track by its Spotify ID from the in-memory cache.

    Args:
    - track_id: The Spotify ID of the track.

    Returns:
    A dictionary containing detailed information about the track, or None if the track is not found.
    """
    spotify_cache = get_spotify_cache_instance()

    if spotify_cache is None:
        print("Spotify cache instance is not available.")
        return None

    if track_id in spotify_cache.tracks_cache:
        track_details = spotify_cache.tracks_cache[track_id]
        track_info = {
            'id': track_id,
            'name': track_details['name'],
            'album': track_details.get('album', 'Unknown Album'),

            # Adjusted to list artist names
            'artists': [artist['name'] for artist in track_details.get('artists', [])],
            'duration_ms': track_details.get('duration_ms', 0),
            'spotify_url': track_details.get('spotify_url', '#'),

            # Providing default values
            'image_url': track_details.get('image_url', 'https://example.com/default_image.png'),
            'metrics': track_details.get('metric')
        }
        return track_info
    else:
        print(f"Track ID {track_id} not found in cache.")
        return None

def get_all_tracks_data_from_cache():
    """
    Retrieves all tracks data from the cache.

    Returns:
        A list of dictionaries, each representing a track.
        Returns an empty list if no data is found or an error occurs.
    """
    try:
        spotify_cache = get_spotify_cache_instance()
        if not spotify_cache:
            logging.error("Spotify cache instance is not available.")
            return []

        all_tracks = list(spotify_cache.tracks_cache.values())
        logging.info(
            f"Successfully retrieved {len(all_tracks)} tracks from cache.")
        return all_tracks
    except Exception as e:
        logging.error(f"Failed to fetch tracks data from cache: {e}")
        return []

def update_track_cache_with_audio_features(sp: Spotify, track_id):
    """
    Fetches and updates the tracks cache with audio features for a specified track.

    Args:
    - sp: An authenticated spotipy.Spotify client.
    - track_id: The Spotify ID of the track.
    """
    spotify_cache = get_spotify_cache_instance()
    if not spotify_cache:
        logging.error("Spotify cache instance is not available.")
        return

    # Fetch audio features for the given track_id
    audio_features = sp.audio_features([track_id])[0]
    if audio_features:
        # Simplify assignment with a dictionary comprehension for relevant audio features
        audio_features_data = {k: audio_features[k] for k in (
            'acousticness', 'danceability', 'energy', 'instrumentalness',
            'liveness', 'loudness', 'speechiness', 'tempo', 'valence')}

        # Update the cache with newly fetched audio features
        if track_id in spotify_cache.tracks_cache:
            spotify_cache.tracks_cache[track_id]["audio_features"] = audio_features_data
        else:
            # If the track isn't in the cache, add it with the audio features
            spotify_cache.tracks_cache[track_id] = {
                "audio_features": audio_features_data}

def update_tracks_cache_with_audio_features_in_bulk(sp: Spotify, track_ids):
    """
    Fetches and updates the global tracks cache with audio features for each track specified in track_ids.

    Args:
    - sp: An authenticated spotipy.Spotify client.
    - track_ids: List of unique track IDs.
    """
    spotify_cache = get_spotify_cache_instance()
    if not spotify_cache:
        logging.error("Spotify cache instance is not available.")
        return

    # Iterate over track_ids in batches of 100
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        audio_features_list = sp.audio_features(batch)

        for features in audio_features_list:
            if features:
                track_id = features['id']
                # Simplify assignment with a dictionary comprehension
                audio_features = {k: features[k] for k in (
                    'acousticness', 'danceability', 'energy', 'instrumentalness',
                    'liveness', 'loudness', 'speechiness', 'tempo', 'valence')}

                # Update the cache with newly fetched audio features
                spotify_cache.tracks_cache[track_id] = spotify_cache.tracks_cache.get(
                    track_id, {})
                spotify_cache.tracks_cache[track_id]["audio_features"] = audio_features

def get_tracks_audio_features_in_bulk(sp, track_ids):
    """
    Retrieves audio features for a list of tracks in bulk from the global tracks_cache. 
    Fetches them from Spotify and updates the cache if audio features are not available.

    Args:
    - sp: An authenticated spotipy.Spotify client.
    - track_ids: A list of Spotify track IDs.

    Returns:
    A dictionary mapping each track ID to its audio features.
    """
    spotify_cache = get_spotify_cache_instance()
    if not spotify_cache:
        logging.error("Spotify cache instance is not available.")
        return {}

    tracks_audio_features = {}
    tracks_with_no_data_in_cache = []

    # Check the cache first
    for track_id in track_ids:
        if "audio_features" in spotify_cache.tracks_cache.get(track_id, {}):
            tracks_audio_features[track_id] = spotify_cache.tracks_cache[track_id]["audio_features"]
        else:
            tracks_with_no_data_in_cache.append(track_id)

    # Update cache for tracks missing audio features
    if tracks_with_no_data_in_cache:
        logging.info("Fetching missing audio features from Spotify.")
        update_tracks_cache_with_audio_features_in_bulk(
            sp, tracks_with_no_data_in_cache)
        # Retrieve newly updated features
        for track_id in tracks_with_no_data_in_cache:
            if "audio_features" in spotify_cache.tracks_cache.get(track_id, {}):
                tracks_audio_features[track_id] = spotify_cache.tracks_cache[track_id]["audio_features"]
    else:
        logging.info(
            "All requested tracks have audio features available in cache.")

    return tracks_audio_features

##----------------- Playlist Specific -------------------##

def get_playlist_data_by_id_from_cache(playlist_id):
    """
    Retrieves data for a specific playlist by its ID from the cache.

    Args:
        playlist_id (str): The Spotify ID of the playlist.

    Returns:
        A dictionary containing the playlist's data if found, None otherwise.
    """
    try:
        spotify_cache = get_spotify_cache_instance()
        if not spotify_cache:
            logging.error("Spotify cache instance is not available.")
            return None

        # Accessing the specific playlist by ID from the playlist_cache
        playlist_data = spotify_cache.playlist_cache.get(playlist_id)
        if playlist_data:
            logging.info(
                f"Playlist data for ID {playlist_id} retrieved from cache.")
            return playlist_data
        else:
            logging.warning(
                f"Playlist with ID {playlist_id} not found in cache.")
            return None
    except Exception as e:
        logging.error(
            f"Failed to fetch playlist {playlist_id} data from cache: {e}")
        return None

def get_all_playlist_data_from_cache():
    """
    Retrieves all playlist data from the cache.

    Returns:
        A list of dictionaries, each representing a playlist.
        Returns an empty list if no data is found or an error occurs.
    """
    try:
        spotify_cache = get_spotify_cache_instance()
        if not spotify_cache:
            logging.error("Spotify cache instance is not available.")
            return []

        # Assuming playlist_cache is a dict of playlists keyed by playlist IDs
        all_playlists = list(spotify_cache.playlist_cache.values())
        logging.info(
            f"Successfully retrieved {len(all_playlists)} playlists from cache.")
        return all_playlists
    except Exception as e:
        logging.error(f"Failed to fetch playlist data from cache: {e}")
        return []

def get_playlist_wise_tracks_information_from_cache(playlist_id):
    """
    Retrieves detailed information for all tracks in a specific playlist by its Spotify ID from the in-memory cache.

    Args:
    - playlist_id: The Spotify ID of the playlist.

    Returns:
    A list of dictionaries, each containing detailed information about a track, or None if the playlist or tracks are not found.
    """
    spotify_cache = get_spotify_cache_instance()

    if spotify_cache is None:
        print("Spotify cache instance is not available.")
        return None

    playlist_data = spotify_cache.playlist_cache.get(playlist_id)
    if not playlist_data:
        print(f"Playlist ID {playlist_id} not found in cache.")
        return None

    track_ids = playlist_data.get('track_ids', [])
    all_tracks_info = []

    for track_id in track_ids:
        track_details = spotify_cache.tracks_cache.get(track_id)
        if track_details:
            track_info = {
                'id': track_id,
                'name': track_details['name'],
                'album': track_details.get('album', 'Unknown Album'),
                'artists': [artist['name'] for artist in track_details.get('artists', [])],
                'duration_ms': track_details.get('duration_ms', 0),
                'spotify_url': track_details.get('spotify_url', '#'),
                'image_url': track_details.get('image_url', 'https://example.com/default_image.png'),
                'metrics': track_details.get('metrics')
            }
            all_tracks_info.append(track_info)
        else:
            print(f"Track ID {track_id} not found in tracks cache.")

    return all_tracks_info

def update_playlist_metrics(playlist_id):
    """
    Calculates metrics for a specific playlist by its ID, using cached track and artist data.

    Args:
    - playlist_id: The Spotify ID of the playlist.

    Returns:
    A dictionary containing metrics for the playlist.
    """
    spotify_cache = get_spotify_cache_instance()

    # Initialize variables to store data
    genres = {}
    artist_counts = {}
    release_years = []
    popularity_scores = []
    audio_features_list = []

    # Check if playlist_id is in the playlist_cache
    if playlist_id not in spotify_cache.playlist_cache:
        print(f"Playlist ID {playlist_id} not found in cache.")
        return {}

    playlist_tracks = spotify_cache.playlist_cache[playlist_id]['track_ids']

    for track_id in playlist_tracks:
        # Fetch track details from tracks_cache
        if track_id in spotify_cache.tracks_cache:
            track = spotify_cache.tracks_cache[track_id]

            # Process track data
            try:
                release_year = int(track['album']['release_date'][:4])
                release_years.append(release_year)
            except KeyError:
                pass  # Handle tracks without release dates

            popularity_scores.append(track.get('popularity', 0))

            # Process artist data
            for artist_id in track['artists']:
                # Fetch artist details from artists_cache
                if artist_id in spotify_cache.artists_cache:
                    artist = spotify_cache.artists_cache[artist_id]
                    artist_name = artist['name']
                    artist_counts[artist_name] = artist_counts.get(
                        artist_name, 0) + 1

                    for genre in artist.get('genres', []):
                        genres[genre] = genres.get(genre, 0) + 1

            # Collect audio features if available
            if 'audio_features' in track:
                audio_features_list.append(track['audio_features'])

    # Calculate metrics
    metrics = {
        'Track Count': len(playlist_tracks),
        'Total Duration': sum([feature['duration_ms'] for feature in audio_features_list]) / 1000,
        'Average Track Duration': np.mean([feature['duration_ms'] for feature in audio_features_list]) / 1000 if audio_features_list else 0,
        'Genre Distribution': genres,
        'Artist Diversity': len(set(artist_counts.keys())),
        'Most Featured Artist(s)': max(artist_counts, key=artist_counts.get) if artist_counts else 'N/A',
        'Release Year Range': f"{min(release_years)} - {max(release_years)}" if release_years else 'N/A',
        'Average Release Year': np.mean(release_years) if release_years else 'N/A',
        'Average Popularity Score': np.mean(popularity_scores) if popularity_scores else 0,
        # Extract average audio features
        'Average Energy': np.mean([feature['energy'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Danceability': np.mean([feature['danceability'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Valence': np.mean([feature['valence'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Acousticness': np.mean([feature['acousticness'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Instrumentalness': np.mean([feature['instrumentalness'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Speechiness': np.mean([feature['speechiness'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Loudness': np.mean([feature['loudness'] for feature in audio_features_list]) if audio_features_list else 0,
        'Average Tempo': np.mean([feature['tempo'] for feature in audio_features_list]) if audio_features_list else 0
    }

    # Update playlist cache
    spotify_cache.playlist_cache[playlist_id]['metrics'] = metrics

def update_playlist_metrics_cache_in_bulk(sp):
    """
    Calculates and updates metrics for each playlist in the global playlist_cache.

    Args:
    - sp: An authenticated spotipy.Spotify client.
    """
    spotify_cache = get_spotify_cache_instance()

    for playlist_id, playlist_data in spotify_cache.playlist_cache.items():
        # Calculate metrics for each playlist
        update_playlist_metrics(playlist_id, sp)

def get_playlist_metric_by_id(playlist_id):
    """
    Returns playlist metric dictionary 

    Args:
    - playlist_id: unique identifier for the playlist

    Returns:
    - dict: Playlist metric dictionary
    """
    spotify_cache = get_spotify_cache_instance()

    try:
        playlist_metric = spotify_cache.playlist_cache[playlist_id]
    except KeyError:
        # Handle the case where the playlist_id does not exist in the cache
        print(f"Playlist with ID {playlist_id} not found in cache.")
        return None

    return playlist_metric
