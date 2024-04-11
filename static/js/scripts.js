$(document).ready(() => {
    const state = {
        userContentFetched: false,
        selectedPlaylistId: null, // Make sure this is properly updated elsewhere in your script
    };

    function loadContent(page) {
        $.ajax({
            url: `${apiService.baseUrl}/content/${page}`,
            type: "GET",
            success: (response) => {
                $('#main-content #content-placeholder').html(response);
                executePageSpecificFunctions(page);
            },
            error: () => {
                $('#main-content #content-placeholder').html("<p>Error loading content.</p>");
            }
        });
    }

    function executePageSpecificFunctions(page) {
        switch (page) {
            case 'playlists':
                fetchAllPlaylists();
                break;
            case 'dashboard':
                console.log("Dashboard under development");
                break;
            default:
                console.error("Invalid page:", page);
        }
    }

    function fetchAllPlaylists() {
        apiService.getAllPlaylists()
            .done((playlists) => {
                templateRenderer.renderPlaylists(playlists);
                setupPlaylistItemListeners();
            })
            .fail(() => {
                console.error("Error fetching playlists.");
            });
    }

    function initNavControls() {
        $('#sidebar-menu .nav-link').on('click', function (e) {
            e.preventDefault();

            const page = $(this).data('page');
            loadContent(page);

            $('#sidebar-menu .nav-link').removeClass('active');
            $(this).addClass('active');
        });
    }

    function initCarouselControls() {
        $(".carousel-control-prev, .carousel-control-next").click(function () {
            const direction = $(this).hasClass("carousel-control-prev") ? "prev" : "next";
            $("#carouselExampleControls").carousel(direction);
        });
    }

    function setupPlaylistItemListeners() {
        $("#playlistsContainer").on("click", ".playlist-item", function () {
            const { playlistId, playlistName } = $(this).data();
            $(".playlist-item").removeClass("selected-playlist");
            $(this).addClass("selected-playlist");
            state.selectedPlaylistId = playlistId; // Update the state with the selected playlist ID
            displayPlaylistDetailsAndTracks(playlistId, playlistName);
        });
    }

    function displayPlaylistDetailsAndTracks(playlistId, playlistName) {
        templateRenderer.displayRandomMusicNoteOrPlaylistName(playlistName);
        apiService.getPlaylistDetails(playlistId)
            .done((details) => templateRenderer.renderPlaylistDetails(details, playlistName))
            .fail(() => $("#playlistDetails").html("<p>Error loading playlist details.</p>"));
        apiService.getAllTracksForPlaylist(playlistId)
            .done((tracks) => templateRenderer.renderTracks(tracks))
            .fail(() => $("#tracks-container").html("<div class='list-group'><p>Error loading tracks.</p></div>"));
        setupActionBar();

        // Track selection mode toggling and track selection
        $('#tracks-container').on('click', '.list-group-item', function (e) {
            if ($('#tracks-container').hasClass('selection-mode')) {
                e.preventDefault(); // Prevent default action
                $(this).toggleClass('selected');
            }
        });

        // This handles clicks on any anchors within .list-group-item to prevent navigation
        $('#tracks-container').on('click', '.list-group-item a', function (e) {
            if ($('#tracks-container').hasClass('selection-mode')) {
                e.preventDefault(); // Prevent the link from being followed
                $(this).closest('.list-group-item').toggleClass('selected');
            }
        });

        $('.track-select').on('click', function (e) {
            e.stopPropagation();
        });
    }

    function setupActionBar() {
        $('#selectTracksBtn').click(function () {
            $('#tracks-container').toggleClass('selection-mode');
            $('#deleteTracksBtn').toggle(); // Optionally, toggle visibility based on selection-mode
        });

        setupDeleteTrackListener();
    }

    function setupDeleteTrackListener() {
        $('#deleteTracksBtn').click(function () {
            let selectedTrackIds = $('#tracks-container .list-group-item.selected').map(function() {
                // Retrieve the track ID stored in data-track-id
                return $(this).data('track-id');
            }).get();
        

            if (state.selectedPlaylistId && selectedTrackIds.length > 0) {
                apiService.deleteTracksFromPlaylists(selectedTrackIds, state.selectedPlaylistId);
            } else {
                console.error('No playlistId defined or no tracks selected. Cannot delete tracks without a valid playlist ID and selected tracks.');
            }
        });
    }

    // Assuming deleteTracksFromPlaylists is defined elsewhere and correctly communicates with the server

    // Initialize UI controls
    initCarouselControls();
    initNavControls();


});
