function isMobile() {
    return /Mobi|Android/i.test(navigator.userAgent);
}


function escapeHtml(unsafe)
{
    if (unsafe == null)
        return "";

    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}


function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}


function isEmpty( el ){
    return !$.trim(el.html())
}


function getSpinnerText(text = 'Loading...') {
   return `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}`;
}


function putSpinnerOnIt(button) {
    button.prop("disabled", true);

    button.html(
        `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`
    );

    button.parents('form').submit();
}


const getDynamicContentRequestTracker = {};
function getDynamicContent(url_address, htmlElement, errorInHtml = false) {
    if (!getDynamicContentRequestTracker[url_address]) {
        getDynamicContentRequestTracker[url_address] = 0;
    }
    const requestId = ++getDynamicContentRequestTracker[url_address];

    $.ajax({
        url: url_address,
        type: 'GET',
        timeout: 10000,
        success: function(data) {
            if (getDynamicContentRequestTracker[url_address] === requestId) {
                $(htmlElement).html(data);
            }
        },
        error: function(xhr, status, error) {
            if (getDynamicContentRequestTracker[url_address] === requestId) {
                getDynamicContent(url_address, htmlElement, errorInHtml);
            }
        }
    });
}


const getDynamicJsonContentRequestTracker = {};
function getDynamicJsonContent(url_address, htmlElement, errorInHtml = false) {
    if (!getDynamicJsonContentRequestTracker[url_address]) {
        getDynamicJsonContentRequestTracker[url_address] = 0;
    }
    const requestId = ++getDynamicJsonContentRequestTracker[url_address];

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
         if (getDynamicJsonContentRequestTracker[url_address] === requestId) {
             $(htmlElement).html(data.message);
         }
       },
       error: function(xhr, status, error) {
            if (getDynamicJsonContentRequestTracker[url_address] === requestId) {
                getDynamicJsonContent(url_address, htmlElement, errorInHtml);
            }
       }
    });
}


function GetPaginationNav(data) {
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


const getTextContentRequestTracker = {};
function getTextContent(url_address, callback, errorInHtml = false) {
    /*
    Allows to return data via callback
    */
    if (!getTextContentRequestTracker[url_address]) {
        getTextContentRequestTracker[url_address] = 0;
    }
    const requestId = ++getTextContentRequestTracker[url_address];

    $.ajax({
        url: url_address,
        type: 'GET',
        timeout: 10000,
        success: function(data) {
            if (getTextContentRequestTracker[url_address] === requestId) {
                callback(data);
            }
        },
        error: function(xhr, status, error) {
            if (getTextContentRequestTracker[url_address] === requestId) {
                getTextContent(url_address, callback, errorInHtml);
            }
        }
    });
}


const getTextJsonRequestTracker = {};
function getTextJson(url_address, callback, errorInHtml = false) {
    /*
    Allows to return data via callback
    */
    if (!getTextJsonRequestTracker[url_address]) {
        getTextJsonRequestTracker[url_address] = 0;
    }
    const requestId = ++getTextJsonRequestTracker[url_address];

    $.ajax({
        url: url_address,
        type: 'GET',
        timeout: 10000,
        success: function(data) {
            if (getTextJsonRequestTracker[url_address] === requestId) {
                callback(data.message);
            }
        },
        error: function(xhr, status, error) {
            if (getTextJsonRequestTracker[url_address] === requestId) {
                getTextJson(url_address, callback, errorInHtml);
            }
        }
    });
}


function fixStupidGoogleRedirects(input_url) {
    if (!input_url) {
        return null;
    }

    if (input_url.includes("www.google.com/url")) {
        const url = new URL(input_url);
        let realURL = url.searchParams.get('q');
        if (realURL) {
            return realURL;
        }
        realURL = url.searchParams.get('url');
        if (realURL) {
            return realURL;
        }
        return input_url;
    }

    if (input_url.includes("www.youtube.com/redirect")) {
        const url = new URL(input_url);
        let redirectURL = url.searchParams.get('q');

        if (redirectURL) {
            return decodeURIComponent(redirectURL);
        }
        else {
            return input_url;
        }
    }

    return input_url;
}


function getHumanReadableNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(1) + "B"; // Billions
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(1) + "M"; // Millions
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + "K"; // Thousands
    }
    return num.toString(); // Small numbers
}
