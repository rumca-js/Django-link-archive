let currentgetIndicators = 0;
function getIndicators(attempt=1) {
    let requestCurrentgetIndicators = ++currentgetIndicators;

    let url = "{% url 'rsshistory:json-indicators' %}";
    
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestCurrentgetIndicators != currentgetIndicators)
           {
               return;
           }
           common_indicators = data.indicators;

           SetMenuStatusLine();
           SetFooterStatusLine();
       },
       error: function(xhr, status, error) {
           if (requestCurrentgetIndicators != currentgetIndicators)
           {
               return;
           }
           
           if (attempt < 3) {
               getIndicators(attempt + 1);
           } else {
           }
       }
    });
}


function getMenuSearchContainer() {
    let link = "{% url 'rsshistory:json-search-container' %}";
    getDynamicJson(link, function(data) {
        processMenuData(data, '#MenuSearchContainer');
    });
}


function getMenuGlobalContainer() {
    let link = "{% url 'rsshistory:json-global-container' %}";
    getDynamicJson(link, function(data) {
        processMenuData(data, '#MenuGlobalContainer');
    });
}


function getMenuPersonalContainer() {
    let link = "{% url 'rsshistory:json-personal-container' %}";
    getDynamicJson(link, function(data) {
        processMenuData(data, '#MenuPersonalContainer');
    });
}

function getMenuTools() {
    let link = "{% url 'rsshistory:json-tools-container' %}";
    getDynamicJson(link, function(data) {
        processMenuData(data, '#MenuToolsContainer');
    });
}


function getMenuUsers() {
    let link = "{% url 'rsshistory:json-users-container' %}";
    getDynamicJson(link, function(data) {
        processMenuData(data, '#MenuUsersContainer');
    });
}


function getBasicPageElements() {
    getIndicators();
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
        getIndicators();
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

    animateToTop();

    performSearch();
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

