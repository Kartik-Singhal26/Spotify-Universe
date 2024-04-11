$(document).ready(() => {
    const state = {
        userContentFetched: false,
        selectedPlaylistId: null,
        selectedPlaylists: [],
        isComparing: false
    };

    function loadContent(page) {
        $.ajax({
            url: `${apiService.baseUrl}/content/${page}`,
            type: "GET",
            success: (response) => {
                console.log("Content loaded successfully.");
                $('#main-content #content-placeholder').html(response);
                executePageSpecificFunctions(page);
            },
            error: () => {
                console.error("Error loading content.");
                $('#main-content #content-placeholder').html("<p>Error loading content.</p>");
            }
        });
    }

    function executePageSpecificFunctions(page) {
        switch (page) {
            case 'playlists':
                console.log("Fetching playlists...");
                fetchAllPlaylists();
                setupComparePlaylistButton();
                break;
            case 'dashboard':
                console.log("Dashboard page under development.");
                break;
            default:
                console.error("Invalid page:", page);
        }
    }

    initNavControls();
    function initNavControls() {
        $('#sidebar-menu .nav-link').on('click', function (e) {
            e.preventDefault();

            const page = $(this).data('page');
            loadContent(page);

            $('#sidebar-menu .nav-link').removeClass('active');
            $(this).addClass('active');
        });
    }

    function fetchAllPlaylists() {
        apiService.getAllPlaylists()
            .done((playlists) => {
                console.log("Playlists fetched successfully.");
                templateRenderer.renderPlaylists(playlists);
                // Playlist related listeners and controls initialization
                setupPlaylistItemListeners();
                makePlaylistsDraggable();
            })
            .fail(() => {
                console.error("Error fetching playlists.");
            });
    }

    function makePlaylistsDraggable() {
        $(".playlist-item").draggable({
            helper: "clone", // Creates a clone of the element for dragging
            appendTo: "body", // Ensures the clone can move outside the playlist container
            revert: "invalid", // Reverts to original position if not dropped in a droppable area
            start: function (event, ui) {
                $(ui.helper).css({
                    "opacity": 0.7, // Making the clone slightly transparent
                    "z-index": 100 // Ensuring it appears above other content
                }).addClass("dragging");
            }
        });
        console.log("Playlists made draggable.");
        initDroppableAreas(); // Ensure this is called after playlists are made draggable
    }

    function setupPlaylistItemListeners() {
        $("#playlistsContainer").on("click", ".playlist-item", function () {
            const playlistId = $(this).data('playlist-id');
            const playlistName = $(this).data('playlist-name');

            if (!state.isComparing) {
                console.log(`Displaying details for playlist ID: ${playlistId}`);
                displayPlaylistDetailsAndTracks(playlistId, playlistName);
            } else {
                updateSelectedPlaylistsForComparison(playlistId, $(this));
            }
        });
    }

    function initDroppableAreas() {
        $(".comparison-side").droppable({
            accept: ".playlist-item", // Specifies which elements are accepted
            tolerance: "pointer", // Uses the pointer's location to determine when the element is over the droppable
            drop: function (event, ui) {
                handleDrop($(this), ui.draggable);
            }
        });
    }

    function handleDrop(droppable, draggable) {
        const playlistId = draggable.data("playlist-id");
    
        // Log dropping a new playlist for comparison
        console.log(`Dropped playlist ID: ${playlistId} for comparison.`);
    
        // Fetch and display the new playlist details, overwriting any existing content
        apiService.getPlaylistDetails(playlistId).then(playlistDetails => {
            templateRenderer.renderPlaylistDetails(playlistDetails, droppable);
        }).catch(error => {
            console.error("Error fetching playlist details:", error);
            droppable.html("<p>Error loading playlist details.</p>");
        });
    }

    function setupComparePlaylistButton() {
        $('#comparePlaylistsBtn').click(function () {
            state.isComparing = !state.isComparing;
            console.log(`Comparison mode: ${state.isComparing ? 'ON' : 'OFF'}`);

            // Empty the playlist and comparison containers
            $('#selected-playlist-container').empty();
            $('#playlistDetails').empty();
            $('#tracks-container').empty();

            // Remove selection highlights from any previously selected playlists
            $('.playlist-item').removeClass('selected-playlist');

            // Reset the list of selected playlists in the state
            state.selectedPlaylists = [];
        });
    }

    function displayPlaylistDetailsAndTracks(playlistId, playlistName) {
        templateRenderer.displayRandomMusicNoteOrPlaylistName(playlistName);
        apiService.getPlaylistDetails(playlistId)
            .done((details) => {
                console.log(`Rendering details for ${playlistName}.`);
                templateRenderer.renderPlaylistDetails(details, '#playlistDetails');
            })
            .fail(() => {
                console.error(`Error loading details for playlist ${playlistName}.`);
                $("#playlistDetails").html("<p>Error loading playlist details.</p>");
            });

        apiService.getAllTracksForPlaylist(playlistId)
            .done((tracks) => {
                console.log(`Rendering tracks for ${playlistName}.`);
                templateRenderer.renderTracks(tracks);
                setupTrackSelectionListeners();
            })
            .fail(() => {
                console.error(`Error loading tracks for playlist ${playlistName}.`);
                $("#tracks-container").html("<div class='list-group'><p>Error loading tracks.</p></div>");
            });
        setupActionBar();
    }

    function setupTrackSelectionListeners() {
        $('#tracks-container').on('click', '.list-group-item', function (e) {
            if ($('#tracks-container').hasClass('selection-mode')) {
                e.preventDefault(); // Prevent default action
                $(this).toggleClass('selected');
                console.log('Track selection toggled.');
            }
        });

        $('.track-select').on('click', function (e) {
            e.stopPropagation();
        });
    }

    function updateSelectedPlaylistsForComparison(playlistId, playlistItem) {
        if (state.selectedPlaylists.includes(playlistId)) {
            state.selectedPlaylists = state.selectedPlaylists.filter(id => id !== playlistId);
            playlistItem.removeClass('selected-playlist');
            console.log(`Playlist ID ${playlistId} deselected for comparison.`);
        } else if (state.selectedPlaylists.length < 2) {
            state.selectedPlaylists.push(playlistId);
            playlistItem.addClass('selected-playlist');
            console.log(`Playlist ID ${playlistId} selected for comparison.`);
        }

        if (state.selectedPlaylists.length === 2) {
            compareSelectedPlaylists(state.selectedPlaylists);
        }
    }

    function setupDeleteTrackListener() {
        $('#deleteTracksBtn').click(function () {
            let selectedTrackIds = $('#tracks-container .list-group-item.selected').map(function () {
                return $(this).data('track-id');
            }).get();

            if (state.selectedPlaylistId && selectedTrackIds.length > 0) {
                console.log('Deleting selected tracks...');
                apiService.deleteTracksFromPlaylists(selectedTrackIds, state.selectedPlaylistId)
                    .done(() => {
                        console.log('Selected tracks deleted successfully.');
                        // Optionally, refresh the playlist details or tracks here
                    })
                    .fail(() => {
                        console.error('Failed to delete selected tracks.');
                    });
            } else {
                console.error('No playlistId defined or no tracks selected. Cannot delete tracks without a valid playlist ID and selected tracks.');
            }
        });
    }

    function setupActionBar() {
        $('#selectTracksBtn').click(function () {
            const isSelectionMode = $('#tracks-container').toggleClass('selection-mode').hasClass('selection-mode');
            $('#deleteTracksBtn').toggle(isSelectionMode);

            // Log the mode change for track selection
            console.log(`Track selection mode: ${isSelectionMode ? 'Enabled' : 'Disabled'}`);

            if (!isSelectionMode) {
                $('#tracks-container .list-group-item').removeClass('selected');
                console.log('All tracks deselected.');
            }
        });

        setupDeleteTrackListener();
    }
});

