
{% include "rsshistory/urls.js" %}


function getBaseScriptVersion() {
   return 12;
}


function getSystemIndicators() {
   getIndicators(function(data) {
       common_indicators = data.indicators;

       SetMenuStatusLine();
       SetFooterStatusLine();
   });
}


function getBasicPageElements() {
    getSystemIndicators();
    getMenuSearchContainer();
    getMenuGlobalContainer();
    getMenuPersonalContainer();
    getMenuTools();
    getMenuUsers();
}


function applyConfiguration() {
    view_display_style = "{{user_config.display_style}}";
    view_display_type = "{{user_config.display_type}}";
    view_show_icons = "{{user_config.show_icons}}" == "True";
    view_small_icons = "{{user_config.small_icons}}" == "True";
    debug_mode = "{{user_config.debug_mode}}" == "True";
    user_age = {{user_config.get_age}};
    entries_direct_links = {{user_config.entries_direct_links}};

    entries_visit_alpha = {{config.entries_visit_alpha}};
    entries_dead_alpha = {{config.entries_dead_alpha}};

    setDisplayMode();
}



///-----
$(document).ready(function() {

    $("#btnFetch").click(function(event) {
        event.preventDefault();
        putSpinnerOnIt($(this));
    });

    getBasicPageElements();
    applyConfiguration();

    setInterval(function() {
        getBasicPageElements();
    }, 300000);
});


/* when user switches tab - this might result in many fetches
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        getSystemIndicators();
    }
});
*/

//-----------------------------------------------
$(document).on('click', '.btnNavigation', function(e) {
    e.preventDefault();

    const currentPage = $(this).data('page');

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('page', currentPage);
    window.history.pushState({}, '', currentUrl);

    var search_term = $(this).data('search') || $('#id_search').val();
    performSearch(search_term, currentPage);
});


//-----------------------------------------------
$(document).on('keydown', "#searchInput", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();

        hideSearchSuggestions();

        performSearch();
    }
});


//-----------------------------------------------
$(document).on('click', '.suggestion-item', function(e) {
    e.preventDefault();

    const searchInput = document.getElementById('searchInput');
    let suggestion_item_value = $(this).data('search')

    searchInput.value = suggestion_item_value;

    hideSearchSuggestions();

    performSearch();
});


//-----------------------------------------------
$(document).on('click', '#dropdownButton', function(e) {
    e.preventDefault();

    let search_suggestions = document.getElementById("search-suggestions");
    if (search_suggestions.style.display == "none") {
        showSearchSuggestions();
    }
    else {
        hideSearchSuggestions();
    }
});

