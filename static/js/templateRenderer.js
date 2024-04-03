const templateRenderer = {
    // Cache DOM elements to avoid repeated selections

    renderPlaylists: function (playlists) {
        let playlistsHtml = '';
        let carouselItemCounter = 0;
        const numItemsPerDisplay = 6;
        playlists.forEach((playlist, index) => {
            if (carouselItemCounter % numItemsPerDisplay === 0) {
                const isActive = carouselItemCounter === 0 ? 'active' : '';
                playlistsHtml += `<div class="carousel-item ${isActive}"><div class="row">`;
            }

            playlistsHtml += `
                <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                    <div class="playlist-item" data-playlist-id="${playlist.id}" data-playlist-name="${playlist.name}">
                        <img src="${playlist.image_url}" class="img-fluid" alt="${playlist.name}">
                    </div>
                </div>`;

            carouselItemCounter++;

            if (carouselItemCounter % numItemsPerDisplay === 0 || index === playlists.length - 1) {
                playlistsHtml += `</div></div>`;
            }
        });

        $("#playlistsContainer").html(playlistsHtml);
    },

    renderPlaylistDetails: function (playlistDetails, playlistName) {
        const mostFeaturedArtists = playlistDetails.metrics['Most Featured Artist(s)'];
        const mostFeaturedArtistsText = Array.isArray(mostFeaturedArtists) ? mostFeaturedArtists.join(', ') : mostFeaturedArtists;

        const playlistDetailsHtml = `
            <h2>${playlistName}</h2>
            <p>${playlistDetails.description}</p>
            <p><strong>Total Tracks:</strong> ${playlistDetails.metrics['Track Count']}</p>
            <p><strong>Total Duration:</strong> ${playlistDetails.metrics['Total Duration']} hrs</p>
            <p><strong>Artist Diversity:</strong> ${playlistDetails.metrics['Artist Diversity']}</p>
            <p><strong>Most Featured Artist(s):</strong> ${mostFeaturedArtistsText}</p>
            <p><strong>Release Year Range:</strong> ${playlistDetails.metrics['Release Year Range']}</p>
        `;

        $("#playlistDetails").html(playlistDetailsHtml);
    },

    renderTracks: function (tracks) {
        let tracksHtml = "<div class='list-group'>";
        tracks.forEach(track => {
            const trackDuration = new Date(track.duration_ms).toISOString().substr(14, 5);
            tracksHtml += `
                <a href="${track.spotify_url}" target="_blank" class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between align-items-center w-100">
                        <div class="track-info d-flex align-items-center">
                            <img src="${track.image_url}" alt="${track.name}" class="img-fluid mr-3" style="width: 50px; height: 50px; object-fit: cover;">
                            <div>
                                <h5 class="mb-1 text-truncate" style="max-width: 300px;">${track.name}</h5>
                                <p class="mb-1" style="font-size: 14px;">${track.artists}</p>
                            </div>
                        </div>
                        <small class="ml-4 text-right track-time" style="font-size: 12px;">${trackDuration}</small>
                    </div>
                </a>
            `;
        });
        tracksHtml += "</div>";

        $("#tracksContainer").html(tracksHtml);
    },

    displayRandomMusicNoteOrPlaylistName: function (playlistName) {
        let contentHtml;
        if (playlistName) {
            contentHtml = `<p>Loading data for ${playlistName}...</p>`;
        } else {
            const musicNotes = ["🎸", "🎻", "🎷", "🎺", "🎹", "🥁", "🎵", "🎶", "♪", "♫", "♬", "🎼", "🎧", "🎤", "📻", "🎫", "💿", "📀", "🔌"];
            const randomNote = musicNotes[Math.floor(Math.random() * musicNotes.length)];
            contentHtml = `<div class="text-center mt-5"><span style="font-size: 100px;">${randomNote}</span><p class="mt-3">Select a playlist to see tracks</p></div>`;
        }

        $("#tracksContainer").html(contentHtml);
    }
};