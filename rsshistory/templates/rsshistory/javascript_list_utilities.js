function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function isEmpty( el ){
    return !$.trim(el.html())
}

function fillPagination(data, text) {
    let totalPages = data.num_pages;
    let count = data.count;
    let currentPage = data.page;

    if (totalPages <= 1) {
        return '';
    }

    let paginationText = `
        <nav aria-label="Page navigation">
            <ul class="pagination">
    `;

    const currentUrl = new URL(window.location);
    currentUrl.searchParams.delete('page');
    const paginationArgs = `${currentUrl.searchParams.toString()}`;

    if (currentPage > 2) {
        paginationText += `
            <li class="page-item">
                <a href="?page=1${paginationArgs}" data-page="1" class="btnFilterTrigger page-link">|&lt;</a>
            </li>
        `;
    }
    if (currentPage > 2) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${currentPage - 1}${paginationArgs}" data-page="${currentPage - 1}" class="btnFilterTrigger page-link">&lt;</a>
            </li>
        `;
    }

    let startPage = Math.max(1, currentPage - 1);
    let endPage = Math.min(totalPages, currentPage + 1);

    for (let i = startPage; i <= endPage; i++) {
        paginationText += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a href="?page=${i}${paginationArgs}" data-page="${i}" class="btnFilterTrigger page-link">${i}</a>
            </li>
        `;
    }

    if (currentPage + 1 < totalPages) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${currentPage + 1}${paginationArgs}" data-page="${currentPage + 1}" class="btnFilterTrigger page-link">&gt;</a>
            </li>
        `;
    }
    if (currentPage + 1 < totalPages) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${totalPages}${paginationArgs}" data-page="${totalPages}" class="btnFilterTrigger page-link">&gt;|</a>
            </li>
        `;
    }

    paginationText += `
            </ul>
            ${currentPage} / ${totalPages} @ ${count} records.
        </nav>
    `;

    return paginationText;
}

function getHideButton() {
    let text = "";

    let button_text = "<button id='hideSuggestions' type='button' class='btn btn-primary float-end'>Hide</button>";
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

    let button_text = getHideButton();
    text += button_text;

    if (items && items.length > 0) {
        $.each(items, function(index, item) {
            var listItem = `
                <li class="list-group-item">
                    <a class="btnFilterTrigger" data-search="${item}" href="?search=${encodeURIComponent(item)}">
                        ${item}
                    </a>
                </li>
            `;

            text += listItem;
        });
    }

    if (items.length > 10)
    {
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

    let button_text = getHideButton();
    text += button_text;

    if (items && items.length > 0) {
        $.each(items, function(index, item) {
            let query = item.search_query

            var listItem = `
                <li class="list-group-item">
                    <a class="btnFilterTrigger" data-search="${query}" href="?search=${encodeURIComponent(query)}">
                        ${query}
                    </a>
                </li>
            `;

            text += listItem;
        });
    }

    if (items.length > 10)
    {
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
            if (requestVersion === currentSearchSuggestions)
            {
                if (attempt < 3) {
                    loadSearchSuggestions(search_term, attempt + 1); 
                }
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
            if (requestVersion === currentSearchHistory) {
                fillSearchHistory(data.histories);
            }
        },
        error: function(xhr, status, error) {
            if (attempt < 3) {
                loadSearchHistory(attempt + 1);
            }
        }
    });
}

let currentLoadRowListContentCounter = 0;

function loadRowListContent(search_term = '', page = '', attempt = 1) {
   $('.btnFilterTrigger').prop("disabled", true);

   const currentUrl = new URL(window.location);
   const currentSearch = currentUrl.searchParams.get('search') || '';

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

   const status_text = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading... ' + url;
   $('#listStatus').html(status_text);

    $.ajax({
        url: url,
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestVersion === currentLoadRowListContentCounter) {
               $('html, body').animate({ scrollTop: 0 }, 'slow');
               fillListData(data);
               $('#listStatus').html("");
               loadSearchHistory();
            }
        },
        error: function(xhr, status, error) {
            if (requestVersion === currentLoadRowListContentCounter) {
                if (attempt < 3) {
                    loadRowListContent(search_term, page, attempt + 1);
                    $('#listStatus').html("Error loading dynamic content, retry");
                }
                else {
                    $('#listStatus').html("Cannot load data from " + url);
                }
            }
        },
        complete: function() {
            $('.btnFilterTrigger').prop("disabled", false);
        }
    });
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

    $('.btnFilterTrigger').prop("disabled", false);

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
var show = getQueryParam('show') || 'true';
var auto_refresh = getQueryParam('auto-refresh') || '';
var search_term = getQueryParam('search') || '';

$('#searchSuggestions').hide();
$('#searchHistory').hide();
$('#searchSyntax').hide();

var search_term_input = $('#filterForm input[name="search"]').val();
if (search_term_input)
{
    loadSearchSuggestions(search_term_input);
}
loadSearchHistory();

// if (user specified search, or show is true), and entrylist is empty
if (search_term || (show !== '0' && show !== 'false')) {
    if (isEmpty($('#listData'))) {
        loadRowListContent();
    }
}

//-----------------------------------------------
// if auto refresh - keep refreshing list - for kiosk mode
if (auto_refresh && !isNaN(auto_refresh)) {
    setInterval(function() {
        loadRowListContent();
    }, parseInt(auto_refresh));
}
