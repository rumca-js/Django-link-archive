{% load static %}

let object_list_data = null;
let original_title = null;


function getHideButton(input_text = "Hide") {
    let text = "";

    let button_text = `<button id='hideSuggestions' type='button' class='btn btn-primary float-end'>${input_text}</button>`;

    text += '<li class="list-group-item">';
    text += button_text;
    text += '</li>';

    return text;
}


function fillSearchSuggestions(items) {
    if (items.length == 0) {
       $('#searchSuggestions').hide();
       return;
    }

    let text = "<ul class='list-group border border-secondary rounded'>";

    let button_text = getHideButton("Hide");
    text += button_text;

    if (items && items.length > 0) {
        $.each(items, function(index, item) {
            let item_escaped = escapeHtml(item);

            var listItem = `
                <div class="list-group-item list-group-item-action">
                    <a class="btnFilterTrigger " data-search="${item_escaped}" href="?search=${encodeURIComponent(item)}">
                       🔍
                        ${item_escaped}
                    </a>
		</div>
            `;

            text += listItem;
        });
    }

    if (items.length > 10)
    {
       let button_text = getHideButton("Hide");
       text += button_text;
    }

    text += '</ul>';

    $('#searchSuggestions').html(text);
}


function fillSearchHistory(items) {
    if (items.length == 0) {
       $('#searchHistory').hide();
       return;
    }

    let text = "<ul class='list-group border border-secondary rounded'>";

    let button_text = getHideButton('Hide');
    text += button_text;

    if (items && items.length > 0) {
        $.each(items, function(index, item) {
            let query = item.search_query
            let item_escaped = escapeHtml(query);

            url = `{% url "rsshistory:user-search-history-remove" %}?search=${encodeURIComponent(query)}`;

            var listItem = `
                <div class="list-group-item list-group-item-action d-flex align-items-center">
                   <a class="btnFilterTrigger" data-search="${item_escaped}" href="?search=${encodeURIComponent(query)}">
                   🔍
                       ${item_escaped}
                   </a>
		   <a href="${url}" class="ms-auto user-history-remove" data-search="${item_escaped}">
                     <img src="{% static 'rsshistory/icons/icons8-trash-multiple-100.png' %}" class="content-icon" />
		   </a>
                </div>
            `;

            text += listItem;
        });
    }

    if (items.length > 10)
    {
       let button_text = getHideButton('Hide');
       text += button_text;
    }

    text += "</ul>";

    $('#searchHistory').html(text);
}


let currentSearchSuggestions = 0;
let showSuggestions = true;

function loadSearchSuggestions(search_term, attempt = 1) {
    let requestVersion = ++currentSearchSuggestions;

    if ("{{search_suggestions_page}}" == "None") {
        return;
    }

    if (!search_term)
    {
        return;
    }

    url = "{{search_suggestions_page}}".replace("placeholder", search_term);

    $.ajax({
        url: url,
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestVersion === currentSearchSuggestions) {
                $('#searchHistory').hide();
                fillSearchSuggestions(data.items);

                if (showSuggestions)
                {
                   $('#searchSuggestions').show();
                }
            }
        },
        error: function(xhr, status, error) {
            if (requestVersion !== currentSearchSuggestions)
            {
                return;
            }
            if (attempt < 3) {
                loadSearchSuggestions(search_term, attempt + 1); 
            }
        }
    });
}


let currentSearchHistory = 0;
function loadSearchHistory(attempt = 1) {
    let requestVersion = ++currentSearchHistory;

    if ("{{search_history_page}}" == "None") {
        $('#searchHistory').html("No history");
        return;
    }

    $.ajax({
        url: "{{search_history_page}}",
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestVersion !== currentSearchHistory) {
                return;
            }
            fillSearchHistory(data.histories);
        },
        error: function(xhr, status, error) {
            if (requestVersion !== currentSearchHistory) {
                return;
            }
            
            if (attempt < 3) {
                loadSearchHistory(attempt + 1);
            }
        }
    });
}


let currentLoadRowListContentCounter = 0;
function loadRowListContent(search_term = '', page = '', attempt = 1) {
   disableFilterButton();

   if (original_title === null) {
      original_title = document.title;
   }

   if (isEmpty($('#listData'))) {
      $('#listData').html(getSpinnerText());
   }

   const currentUrl = new URL(window.location);
   const currentSearch = currentUrl.searchParams.get('search') || '';

   document.title = original_title + " " + currentSearch;

   page = page || currentUrl.searchParams.get('page') || '1';

   if (!search_term) {
       search_term = currentSearch;
   } else if (currentSearch !== search_term) {
       page = '1';
   }

   currentUrl.searchParams.set('search', search_term);
   currentUrl.searchParams.set('page', page);

    if (search_term) {
        $('#id_search').val(search_term);
    }

   window.history.pushState({}, '', currentUrl);

   const url = `{{query_page}}?${currentUrl.searchParams.toString()}`;

   const requestVersion = ++currentLoadRowListContentCounter;

   const status_text = getSpinnerText();
   //$('#listStatus').show();
   $('#footerStatus').show();
   //$('#listStatus').html(status_text);
   $('#footerStatus').html(status_text);

    $.ajax({
        url: url,
        type: 'GET',
        timeout: 55000,
        success: function(data) {
            if (requestVersion !== currentLoadRowListContentCounter) {
               return;
            }
            $('html, body').animate({ scrollTop: 0 }, 'slow');
            object_list_data = data;
            fillListData();
            $('#listStatus').html("");
            $('#listStatus').hide();
            $('#footerStatus').html("");
            $('#footerStatus').hide();

            loadSearchHistory();
        },
        error: function(xhr, status, error) {
            if (requestVersion !== currentLoadRowListContentCounter) {
                return;
            }

            $('#listStatus').show();
            $('#footerStatus').show();

            if (attempt < 3) {
                loadRowListContent(search_term, page, attempt + 1);
            }
            else {
                $('#listStatus').html("Error loading list content");
                $('#footerStatus').html("Error loading list content");
            }
        },
        complete: function() {
	    enableFilterButton();
        }
    });
}


function enableFilterButton() {
   const status_text = '🔍';
    $('#btnFilterForm').html(status_text);

    $('.btnFilterTrigger').prop("disabled", false);
}

function disableFilterButton() {
   const status_text = getSpinnerText("");
    $('#btnFilterForm').html(status_text);

    $('.btnFilterTrigger').prop("disabled", true);
}


function isShowRequired() {
   var show = false;
   
   if (getQueryParam('show') === 'true' || getQueryParam('show') === 'True') {
       show = true;
   }
   
   var $filterForm = $('#filterForm');
   
   if ($filterForm.length === 0) {
       // No filterForm exists
       show = true;
   } else if ($filterForm.data('auto-fetch') !== "True") {
       show = false;
   }

   return show;
}


//-----------------------------------------------
$(document).on('click', '.btnFilterTrigger', function(e) {
    e.preventDefault();
    
    var search_term = $(this).data('search') || $('#id_search').val();
    var page = $(this).data('page')

    $('#searchSuggestions').hide();
    $('#searchHistory').hide();
    $('#searchSyntax').hide();

    showSuggestions = false;

    loadRowListContent(search_term, page);
});


//-----------------------------------------------
$(document).on('click', '.btnNavigation', function(e) {
    e.preventDefault();
    
    let page = $(this).data("page");
    let currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("page", page);
    window.history.pushState({}, '', currentUrl);

    var search_term = $(this).data('search') || $('#id_search').val();
    loadRowListContent(search_term, page);
});


//-----------------------------------------------
$(document).on('click', '#btnSearchHistory', function(e) {
    e.preventDefault();

    $('#searchSuggestions').hide();
    $('#searchHistory').toggle();
    $('#searchSyntax').hide();
});


//-----------------------------------------------
// Bind to the input event of the search input within the form
$('#filterForm input[name="search"]').on('input', function() {
    var search_term = $('#filterForm input[name="search"]').val();

    //disableFilterButton();

    $('#searchSyntax').hide();
    $('#searchSuggestions').empty();
    $('#searchHistory').hide();

    showSuggestions = true;

    if (search_term) {
        loadSearchSuggestions(search_term);
    }
});


//-----------------------------------------------
// Bind to the button syntax
$(document).on("click", '#btnSearchSyntax', function(e) {
    e.preventDefault();

    $('#searchSyntax').toggle();
    $('#searchHistory').hide();
    $('#searchSuggestsions').hide();
});


$(document).on("click", '#hideSuggestions', function(e) {
    $('#searchSuggestions').hide();
    $('#searchHistory').hide();
});


$(document).on("click", '#hideHistory', function(e) {
    $('#searchSuggestions').hide();
    $('#searchHistory').hide();
});

//-----------------------------------------------
// Do it now

var auto_refresh = getQueryParam('auto-refresh') || '';
var search_term = getQueryParam('search') || '';
var show = isShowRequired();

$('#searchSuggestions').hide();
$('#searchHistory').hide();
$('#searchSyntax').hide();

loadSearchHistory();

// if (user specified search, or show is true), and entrylist is empty
if (search_term || show) {
   loadRowListContent();
}

//-----------------------------------------------
// if auto refresh - keep refreshing list - for kiosk mode
if (auto_refresh && !isNaN(auto_refresh)) {
    setInterval(function() {
        loadRowListContent();
    }, parseInt(auto_refresh));
}
