import logging
import json
import os
from spotipy import Spotify  # Ensure spotipy and other necessary packages are imported
from app import auth_manager  # You might need to adjust this import based on your project structure

# You might need to adjust these paths based on your project structure and how you manage configuration
basedir = os.path.abspath(os.path.dirname(__file__))
project_basedir = os.path.join(basedir, os.pardir)
json_file_path = os.path.join(project_basedir, 'playlists_data.json')

def get_user_playlists_with_tracks(sp: Spotify):
    """
     Fetches playlists and their tracks for the current user from Spotify.

    Args:
    - sp: An authenticated spotipy.Spotify client.

    Returns:
    A list of playlist data including playlist details and tracks.
    """
    playlists_data = []
    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists['items']:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        playlist_images = playlist['images']
        playlist_image_url = playlist_images[0]['url'] if playlist_images else None

        playlist_tracks = []
        tracks_response = sp.playlist_tracks(playlist_id, limit=100)
        while tracks_response:
            for item in tracks_response['items']:
                track = item['track']
                if track is not None:
                    track_album_images = track['album']['images']
                    track_image_url = track_album_images[0]['url'] if track_album_images else None

                    track_info = {
                        'name': track['name'],
                        'artist': ', '.join(artist['name'] for artist in track['artists']),
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'spotify_url': track['external_urls']['spotify'],
                        'image_url': track_image_url
                    }
                    playlist_tracks.append(track_info)
            
            if tracks_response['next']:
                tracks_response = sp.next(tracks_response)
            else:
                tracks_response = None

        playlists_data.append({
            'id': playlist_id,
            'name': playlist_name,
            'image_url': playlist_image_url,
            'tracks': playlist_tracks
        })

    return playlists_data

def fetch_and_cache_playlists(sp: Spotify, auth_manager, json_file_path: str):
    """
    Fetches and caches the playlist data, returning it. This function can be reused across different routes.
    
    Args:
    - sp: An authenticated spotipy.Spotify client.
    - auth_manager: The authentication manager for Spotify.
    - json_file_path: The file path for caching playlist data.
    
    Returns:
    The fetched playlist data or None if fetching fails.
    """
    logging.info("Fetching playlists.")
    if not auth_manager.get_cached_token():
        logging.warning("User not authenticated.")
        return None
    
    try:
        if os.path.exists(json_file_path):
            logging.info("Playlists data file found, loading from file.")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                playlists_data = json.load(f)
        else:
            logging.info("Playlists data file not found, fetching playlists from Spotify.")
            playlists_data = get_user_playlists_with_tracks(sp)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(playlists_data, f, ensure_ascii=False, indent=4)
            logging.info("Playlist data updated")
        return playlists_data
    except Exception as e:
        logging.error(f"Error handling playlists data: {e}")
        return None

def calculate_user_stats(sp):
    """Calculates and returns user statistics based on their playlists."""
    playlists_data = fetch_and_cache_playlists(sp, auth_manager, json_file_path)
    if not playlists_data:
        return ({
            'num_playlists': 0,
            'num_unique_tracks': 0,
            'num_unique_artists': 0
        })

    num_playlists = len(playlists_data)
    unique_tracks = set()
    unique_artists = set()

    for playlist in playlists_data:
        tracks = playlist.get('tracks', [])
        for track in tracks:
            unique_tracks.add(track['name'])

            # Split the 'artist' string by comma and strip any whitespace around the names
            artists = track['artist'].split(',')
            for artist in artists:
                # Strip removes leading/trailing whitespace to clean up artist names
                unique_artists.add(artist.strip())

    return ({
        'num_playlists': num_playlists,
        'num_unique_tracks': len(unique_tracks),
        'num_unique_artists': len(unique_artists)
    })