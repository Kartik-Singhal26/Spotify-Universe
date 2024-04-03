$(document).ready(() => {
    const state = {
        userContentFetched: false
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
                console.error("Error loading content.");
            }
        });
    }

    function executePageSpecificFunctions(page) {
        switch (page) {
            case 'playlists':
                fetchAllPlaylists();
                break;
            case 'dashboard':
                console.log("Under development");
                break;
            default:
                console.error("Invalid page:", page);
        }
    }

    function fetchAllPlaylists() {
        apiService.getAllPlaylists()
            .done(function (playlists) {
                templateRenderer.renderPlaylists(playlists);
                setupPlaylistItemListeners();
            })
            .fail(function () {
                console.error("Error fetching playlists.");
            });
    }

    initCarouselControls();
    initNavControls();

    function initNavControls() {
        $('#sidebar-menu .nav-link').on('click', function (e) {
            e.preventDefault(); // Prevent default link behavior

            const page = $(this).data('page'); // Get the data-page value
            loadContent(page); // Load the content for the clicked section

            // Update active state on the sidebar
            $('#sidebar-menu .nav-link').removeClass('active'); // Remove active class from all links
            $(this).addClass('active'); // Add active class to the clicked link
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
            console.log("click");
            $(".playlist-item").removeClass("selected-playlist");
            $(this).addClass("selected-playlist");
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
            .fail(() => $("#tracksContainer").html("<div class='list-group'><p>Error loading tracks.</p></div>"));
    }
});
