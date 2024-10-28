    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    function fillPagination(data, text) {
        let totalPages = data.num_pages;
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

        if (currentPage > 1) {
            paginationText += `
                <li class="page-item">
                    <a href="?page=1${paginationArgs}" data-page="1" class="btnFilterTrigger page-link">|&lt;</a>
                </li>
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

        if (currentPage < totalPages) {
            paginationText += `
                <li class="page-item">
                    <a href="?page=${currentPage + 1}${paginationArgs}" data-page="${currentPage + 1}" class="btnFilterTrigger page-link">&gt;</a>
                </li>
                <li class="page-item">
                    <a href="?page=${totalPages}${paginationArgs}" data-page="${totalPages}" class="btnFilterTrigger page-link">&gt;|</a>
                </li>
            `;
        }

        paginationText += `
                </ul>
            </nav>
        `;

        return paginationText;
    }

    function fillUserSearchSuggestions(items) {
        if (items.length == 0) {
           $('#searchSuggestions').hide();
           return;
	}
        let text = "<ul class='list-group border border-secondary rounded'>";

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

        let button_text = "<button id='hideHistory' type='button' class='btn btn-primary'>Hide</button>";
        text += '<li class="list-group-item">';
	text += button_text;
        text += '</li>';

        text += '</ul>';

        $('#searchSuggestions').html(text);

        $(document).on("click", '#hideSuggestions', function(e) {
            $('#searchSuggestions').hide();
        });
    }

    function fillUserSearchHistory(items) {
        if (items.length == 0) {
           $('#searchHistory').hide();
           return;
	}

        let text = "<ul class='list-group border border-secondary rounded'>";

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

        let button_text = "<button id='hideHistory' type='button' class='btn btn-primary'>Hide</button>";
        text += '<li class="list-group-item">';
	text += button_text;
        text += '</li>';

	text += "</ul>";

        $('#searchHistory').html(text);

        $(document).on("click", '#hideHistory', function(e) {
            $('#searchHistory').hide();
        });
    }

    let loadRowListContentCounter = 0;

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

       window.history.pushState({}, '', currentUrl);

       const url = `{{query_page}}?${currentUrl.searchParams.toString()}`;

       const requestVersion = ++loadRowListContentCounter;

       const status_text = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading... ' + url;
       $('#listStatus').html(status_text);

        $.ajax({
            url: url,
            type: 'GET',
            timeout: 15000,
            success: function(data) {
                if (requestVersion === loadRowListContentCounter) {
                   $('html, body').animate({ scrollTop: 0 }, 'slow');
                   fillListData(data);
                   $('#listStatus').html("");
                   loadUserSearchHistory();
                }
            },
            error: function(xhr, status, error) {
                if (requestVersion === loadRowListContentCounter) {
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

    function isEmpty( el ){
        return !$.trim(el.html())
    }

    $(document).on("click", '#btnSearchSyntax', function(e) {
        e.preventDefault();

        $('#searchSyntax').toggle();
        $('#searchHistory').hide();
        $('#searchSuggestsions').hide();
    });
