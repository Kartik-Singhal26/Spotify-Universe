const apiService = (function() {
    const baseUrl = "http://127.0.0.1:5000";

    // Fetch all playlists
    const getAllPlaylists = () => {
        return $.ajax({
            url: `${baseUrl}/get-all-playlists`,
            type: "GET",
            dataType: "json"
        });
    };

    // Fetch playlist details
    const getPlaylistDetails = (playlistId) => {
        return $.ajax({
            url: `${baseUrl}/get-playlist/${playlistId}`,
            type: "GET",
            dataType: "json"
        });
    };

    // Fetch all tracks for a playlist
    const getAllTracksForPlaylist = (playlistId) => {
        return $.ajax({
            url: `${baseUrl}/get-all-tracks-for-playlist/${playlistId}`,
            type: "GET",
            dataType: "json"
        });
    };

    // Public API
    return {
        getAllPlaylists,
        getPlaylistDetails,
        getAllTracksForPlaylist
    };
})();
