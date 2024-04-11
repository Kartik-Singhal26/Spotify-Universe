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

    const deleteTracksFromPlaylists = (trackIDs, playlistID) => {
        // Assuming `apiService.baseUrl` is defined elsewhere and accessible
        fetch(`${baseUrl}/playlist/delete-tracks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Assuming the server expects both trackIds and playlistID in the request body
            body: JSON.stringify({ trackIds: trackIDs, playlistId: playlistID }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            // Here you can add code to remove the tracks from the UI or notify the user
            // For example, reload the track list to reflect the changes
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    // Public API
    return {
        getAllPlaylists,
        getPlaylistDetails,
        getAllTracksForPlaylist,
        deleteTracksFromPlaylists,
        baseUrl
    };
})();
