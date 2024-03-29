import json
import logging
from spotipy import Spotify
import os
import time

class SpotifyCache:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.tracks_cache = {}
        self.artists_cache = {}
        self.playlist_cache = {}
        self.last_updated = 0  # Timestamp of the last cache update
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.playlist_cache = data.get('playlists_data', {})
                self.tracks_cache = data.get('tracks_details', {})
                self.artists_cache = data.get('artists_details', {})
                self.last_updated = data.get('last_updated', time.time())  # Use current time if not available
            logging.info("Cache loaded from file.")
        else:
            logging.info("Cache file not found, starting with empty caches.")
            self.last_updated = time.time()

    def update_cache(self, playlists_data, tracks_details, artists_details):
        """
        Update the Spotify cache with playlists, tracks, and artists data.

        Args:
        - playlists_data (dict): A dictionary containing playlists data.
        - tracks_details (dict): A dictionary containing tracks details.
        - artists_details (dict): A dictionary containing artists details.

        Returns:
        - None
        """
        self.playlist_cache = playlists_data
        self.tracks_cache = tracks_details
        self.artists_cache = artists_details
        self.last_updated = time.time()
        logging.info("Cache updated with latest data from spotify.")
        self.save_cache_to_file()

    def save_cache_to_file(self):
        data_to_save = {
            'playlists_data': self.playlist_cache,
            'tracks_details': self.tracks_cache,
            'artists_details': self.artists_cache,
            'last_updated': self.last_updated
        }
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            logging.info("Cache successfully saved to file.")
        except Exception as e:
            logging.error(f"Failed to save cache to file: {e}")

    def is_cache_valid(self, max_age_seconds=86400):  # Default to 24 hours
        """
        Checks if the cache is still valid based on its age and whether it contains essential data.

        Args:
        - max_age_seconds: Maximum allowed age of the cache in seconds.

        Returns:
        bool: True if the cache is valid, False otherwise.
        """
        # Check if cache has been updated within the allowed age
        current_time = time.time()
        is_age_valid = (current_time - self.last_updated) < max_age_seconds
        
        # Check if essential data is present in the cache
        is_data_present = bool(self.playlist_cache and self.tracks_cache and self.artists_cache)

        return is_age_valid and is_data_present