$(document).ready(function () {

    let userContentFetched = false;

    function loadContent(page) {
        $.ajax({
            url: `/content/${page}`,
            type: "GET",
            success: function(response) {
                $('#main-content #content-placeholder').html(response);
            },
            error: function() {
                $('#main-content #content-placeholder').html("<p>Error loading content.</p>");
                console.error("Error loading content.");
            }
        });
    }


    // Initial load of content
    loadContent('playlists');

    // Function to fetch all playlists
    function fetchAllPlaylists() {
        if (!userContentFetched) {
            apiService.getAllPlaylists()
                .done(function (playlists) {
                    renderPlaylists(playlists);
                    userContentFetched = true;
                })
                .fail(function () {
                    console.error("Error fetching playlists.");
                });
        }
    }

    // Call to fetch all playlists only if they haven't been fetched yet
    fetchAllPlaylists();

    // Function to render playlists
    function renderPlaylists(playlists) {
        var playlistsHtml = '';
        playlists.forEach(function (playlist, index) {
            var isActive = index === 0 ? 'active' : '';
            playlistsHtml += `
                <div class="carousel-item ${isActive}">
                    <div class="row">
                        <div class="col-lg-3 col-md-4 col-sm-6">
                            <div class="playlist-item" data-playlist-id="${playlist.id}" data-playlist-name="${playlist.name}">
                                <img src="${playlist.image_url}" class="img-fluid" alt="${playlist.name}">
                                <div class="carousel-caption d-none d-md-block">${playlist.name}</div>
                            </div>
                        </div>
                    </div>
                </div>`;
        });
        $("#playlistsContainer").html(playlistsHtml);
    }

    // Click event for navigation links
    $('#sidebar-menu .nav-link').click(function (e) {
        e.preventDefault();
        var page = $(this).data('page');
        loadContent(page);
    });

    // Function to display playlist details and tracks
    function displayPlaylistDetailsAndTracks(playlistId, playlistName) {
        displayRandomMusicNoteOrPlaylistName(playlistName);

        // Fetch playlist details
        apiService.getPlaylistDetails(playlistId)
            .done(function (playlistDetails) {
                renderPlaylistDetails(playlistDetails, playlistName);
            })
            .fail(function () {
                console.error("Error fetching playlist details.");
                $("#playlistDetails").html("<p>Error loading playlist details.</p>");
            });

        // Fetch tracks for the selected playlist
        apiService.getAllTracksForPlaylist(playlistId)
            .done(function (tracks) {
                renderTracks(tracks);
            })
            .fail(function () {
                console.error("Error fetching tracks.");
                $("#tracksContainer").html("<div class='list-group'><p>Error loading tracks.</p></div>");
            });
    }

    // Function to render playlist details
    function renderPlaylistDetails(playlistDetails, playlistName) {
        var mostFeaturedArtists = playlistDetails.metrics['Most Featured Artist(s)'];
        var mostFeaturedArtistsText = Array.isArray(mostFeaturedArtists) ? mostFeaturedArtists.join(', ') : mostFeaturedArtists;

        var playlistDetailsHtml = `
            <h2>${playlistName}</h2>
            <p>${playlistDetails.description}</p>
            <p><strong>Total Tracks:</strong> ${playlistDetails.metrics['Track Count']}</p>
            <p><strong>Total Duration:</strong> ${playlistDetails.metrics['Total Duration']} hrs</p>
            <p><strong>Artist Diversity:</strong> ${playlistDetails.metrics['Artist Diversity']}</p>
            <p><strong>Most Featured Artist(s):</strong> ${mostFeaturedArtistsText}</p>
            <p><strong>Release Year Range:</strong> ${playlistDetails.metrics['Release Year Range']}</p>
        `;
        $("#playlistDetails").html(playlistDetailsHtml);
    }

    // Function to render tracks
    function renderTracks(tracks) {
        var tracksHtml = "<div class='list-group'>";
        tracks.forEach(function (track) {
            var trackDuration = new Date(track.duration_ms).toISOString().substr(14, 5);
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
                        <div class="ml-4 text-right">
                            <small class="track-time" style="font-size: 12px;">${trackDuration}</small>
                        </div>
                    </div>
                </a>
            `;
        });
        tracksHtml += "</div>";
        $("#tracksContainer").html(tracksHtml);
    }

    // Function to display a random music note or playlist name
    function displayRandomMusicNoteOrPlaylistName(playlistName) {
        if (playlistName) {
            $("#tracksContainer").html(`<p>Loading data for ${playlistName}...</p>`);
        } else {
            var musicNotes = ["🎸", "🎻", "🎷", "🎺", "🎹", "🥁", "🎵", "🎶", "♪", "♫", "♬", "🎼", "🎧", "🎤", "📻", "🎫", "💿", "📀", "🔌"];
            var randomNote = musicNotes[Math.floor(Math.random() * musicNotes.length)];
            $("#tracksContainer").html(`<div class="text-center mt-5"><span style="font-size: 100px;">${randomNote}</span><p class="mt-3">Select a playlist to see tracks</p></div>`);
        }
    }

    // Handle playlist item click event
    $("#playlistsContainer").on("click", ".playlist-item", function () {
        var playlistId = $(this).data("playlist-id");
        var playlistName = $(this).data("playlist-name");
        displayPlaylistDetailsAndTracks(playlistId, playlistName);
    });

    // Move carousel to the previous item
    $(".carousel-control-prev").on("click", function () {
        $("#carouselExampleControls").carousel("prev");
    });

    // Move carousel to the next item
    $(".carousel-control-next").on("click", function () {
        $("#carouselExampleControls").carousel("next");
    });

    $("#playlistsContainer").on("click", ".playlist-item", function () {
        $(".playlist-item").removeClass("selected-playlist");
        $(this).addClass("selected-playlist");
    });
});
