// library code

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}


function isMobile() {
    return /Mobi|Android/i.test(navigator.userAgent);
}


function escapeHtml(unsafe)
{
    if (unsafe == null)
        return "";

    unsafe = String(unsafe);

    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}


function createLinks(inputText) {
    const urlRegex = /(?<!<a[^>]*>)(https:\/\/[a-zA-Z0-9-_\.\/]+)(?!<\/a>)/g;
    const urlRegex2 = /(?<!<a[^>]*>)(http:\/\/[a-zA-Z0-9-_\.\/]+)(?!<\/a>)/g;

    inputText = inputText.replace(urlRegex, (match, url) => {
        return `<a href="${url}" target="_blank">${url}</a>`;
    });

    inputText = inputText.replace(urlRegex2, (match, url) => {
        return `<a href="${url}" target="_blank">${url}</a>`;
    });

    return inputText;
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


function GetPaginationNav(data) {
    let totalPages = data.num_pages;
    let totalRows = data.count;
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
                <a href="?page=1&${paginationArgs}" data-page="1" class="btnNavigation page-link">|&lt;</a>
            </li>
        `;
    }
    if (currentPage > 2) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${currentPage - 1}&${paginationArgs}" data-page="${currentPage - 1}" class="btnNavigation page-link">&lt;</a>
            </li>
        `;
    }

    let startPage = Math.max(1, currentPage - 1);
    let endPage = Math.min(totalPages, currentPage + 1);

    for (let i = startPage; i <= endPage; i++) {
        paginationText += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a href="?page=${i}&${paginationArgs}" data-page="${i}" class="btnNavigation page-link">${i}</a>
            </li>
        `;
    }

    if (currentPage + 1 < totalPages) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${currentPage + 1}&${paginationArgs}" data-page="${currentPage + 1}" class="btnNavigation page-link">&gt;</a>
            </li>
        `;
    }
    if (currentPage + 1 < totalPages) {
        paginationText += `
            <li class="page-item">
                <a href="?page=${totalPages}&${paginationArgs}" data-page="${totalPages}" class="btnNavigation page-link">&gt;|</a>
            </li>
        `;
    }

    paginationText += `
            </ul>
            ${currentPage} / ${totalPages} @ ${totalRows} records.
        </nav>
    `;

    return paginationText;
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


function parseDate(inputDate) {
    return inputDate.toLocaleString();
}


class InputContent {
  constructor(text) {
    this.text = text;
  }

  htmlify() {
    this.text = this.stripHtmlAttributes();
    this.text = this.linkify("https://");
    this.text = this.linkify("http://");
    return this.text;
  }

  stripHtmlAttributes() {
    const parser = new DOMParser();
    const doc = parser.parseFromString(this.text, "text/html");

    const walk = (node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.tagName.toLowerCase() === "a") {
          const href = node.getAttribute("href");
          node.getAttributeNames().forEach(attr => node.removeAttribute(attr));
          if (href) node.setAttribute("href", href);
        } else if (node.tagName.toLowerCase() === "img") {
          const src = node.getAttribute("src");
          node.getAttributeNames().forEach(attr => node.removeAttribute(attr));
          if (src) node.setAttribute("src", src);
        } else {
          node.getAttributeNames().forEach(attr => node.removeAttribute(attr));
        }
      }
      for (let child of node.childNodes) {
        walk(child);
      }
    };

    walk(doc.body);
    return doc.body.innerHTML;
  }

  linkify(protocol = "https://") {
    let text = this.text;

    if (!text.includes(protocol)) {
        return text;
    }

    let result = "";
    let i = 0;

    while (i < text.length) {
        const pattern = new RegExp(`${protocol}\\S+(?![\\w.])`);
        const match = text.slice(i).match(pattern);

        if (match && match.index === 0) {
            const url = match[0];
            const precedingChars = text.slice(Math.max(0, i - 10), i);

            if (!precedingChars.includes('<a href="') && !precedingChars.includes("<img")) {
                result += `<a href="${url}">${url}</a>`;
            } else {
                result += url;
            }

            i += url.length;
        } else {
            result += text[i];
            i += 1;
        }
    }

    return result;
  }
}


/**
 * services
 */


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


function sanitizeLink(link) {
   link = link.trimStart();

   if (link.endsWith("/")) {
      link = link.slice(0, -1);
   }
   if (link.endsWith(" ")) {
      link = link.slice(0, -1);
   }

   link = fixStupidGoogleRedirects(link);

   return link;
}


function getYouTubeVideoId(url) {
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;

        if (hostname.includes("youtu.be")) {
            return urlObj.pathname.slice(1);
        }

        if (urlObj.searchParams.has("v")) {
            return urlObj.searchParams.get("v");
        }

        const paths = urlObj.pathname.split("/");
        const validPrefixes = ["embed", "shorts", "v"];
        if (validPrefixes.includes(paths[1]) && paths[2]) {
            return paths[2];
        }

        return null;
    } catch (e) {
        return null;
    }
}


function getYouTubeChannelId(url) {
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;

        if (urlObj.searchParams.has("channel_id")) {
            return urlObj.searchParams.get("channel_id");
        }

        return null;
    } catch (e) {
        return null;
    }
}


function getYouTubeChannelUrl(url) {
    let id = getYouTubeChannelId(url);
    if (id)
        return `https://www.youtube.com/channel/${id}`;
}


function getYouTubeEmbedDiv(youtubeUrl) {
    const videoId = getYouTubeVideoId(youtubeUrl);
    if (videoId) {
        const embedUrl = `https://www.youtube.com/embed/${videoId}`;
        const frameHtml = `
            <div class="youtube_player_container mb-4">
                <iframe 
                    src="${embedUrl}" 
                    frameborder="0" 
                    allowfullscreen 
                    class="youtube_player_frame w-100" 
                    style="aspect-ratio: 16 / 9;"
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
        `;
        return frameHtml;
    }
}


function getChannelUrl(url) {
    let channelid = null;
    if (!url)
        return;

    channelid = getYouTubeChannelUrl(url);
    if (channelid)
        return channelid;
}


/**
 Specific
*/


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


const getDynamicJsonRequestTracker = {};
function getDynamicJson(url_address, callback=null, errorInHtml = false) {
    if (!getDynamicJsonRequestTracker[url_address]) {
        getDynamicJsonRequestTracker[url_address] = 0;
    }
    const requestId = ++getDynamicJsonRequestTracker[url_address];

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
         if (callback && getDynamicJsonRequestTracker[url_address] === requestId) {
             callback(data);
         }
       },
       error: function(xhr, status, error) {
            if (getDynamicJsonRequestTracker[url_address] === requestId) {
                getDynamicJson(url_address, callback, errorInHtml);
            }
       }
    });
}
