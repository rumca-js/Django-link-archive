{% load static %}


let entry_json_data = null;
let entry_dislike_data = null;
let is_downloading = false;


function getEditButton() {
    return `<button id="editTagsButton"><img src="{% static 'rsshistory/icons/icons8-edit-100.png' %}" class="content-icon" /></button>`;
}


function getDownloadingText(text = "Downloading...") {
    return `<span class="bg-warning text-dark"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></span> ${text}`;
}


let currentIsDownloading = 0;
function fillIsEntryDownloaded(attempt = 1) {
    let requestIsDownloading = ++currentIsDownloading;

    $.ajax({
        url: "{% url 'rsshistory:entry-status' object.id %}",
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestIsDownloading != currentIsDownloading) {
                return;
            }
            is_downloading = data.is_downloading;

            if (is_downloading) {
                const text = getDownloadingText("Downloading...");
                $('#entryDownloadContainer').html(text);
            }
            else {
                $('#entryDownloadContainer').html("");
            }

            is_updating = data.is_updating;
            if (is_updating) {
                const text = getDownloadingText("Fetching link data...");
                $('#entryUpdateContainer').html(text);
            }
            else {
                $('#entryUpdateContainer').html("");
            }
        },
        error: function(xhr, status, error) {
            if (requestIsDownloading != currentIsDownloading) {
                return;
            }
            if (attempt < 3) {
                fillIsEntryDownloaded(attempt + 1);
            }
        }
    });
}


function loadEntryDynamicDetails(attempt = 1) {
    getDynamicContent("{% url 'rsshistory:get-entry-details' object.id %}", "#bodyBlock", 1, true);
}


// TODO move to library
function formatNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(1) + "B"; // Billions
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(1) + "M"; // Millions
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + "K"; // Thousands
    }
    return num.toString(); // Small numbers
}


function fillDislike() {
    let parameters = $('#entryParameters').html();

    let { thumbs_up, thumbs_down, view_count, upvote_ratio, upvote_view_ratio } = entry_dislike_data;

    let text = [];

    if (thumbs_up) text.push(`<div class="text-nowrap mx-1">👍${formatNumber(thumbs_up)}</div>`);
    if (thumbs_down) text.push(`<div class="text-nowrap mx-1">👎${formatNumber(thumbs_down)}</div>`);
    if (view_count) text.push(`<div class="text-nowrap mx-1">👁${formatNumber(view_count)}</div>`);

    if (upvote_ratio) text.push(`<div class="text-nowrap mx-1">👍/👎${parseFloat(upvote_ratio).toFixed(2)}</div>`);
    if (upvote_view_ratio) text.push(`<div class="text-nowrap mx-1">👍/👁${parseFloat(upvote_view_ratio).toFixed(2)}</div>`);

    parameters = `${parameters} ${text.join(" ")}`;

    $('#entryParameters').html(parameters);
}


let currentloadDislikeData = 0;
function loadDislikeData(attempt = 1) {
    let requestloadDislikeData = ++currentloadDislikeData;
    let url_address = "{% url 'rsshistory:entry-dislikes' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestloadDislikeData != currentloadDislikeData) {
               return;
           }
           if (data) {
               entry_dislike_data = data;
               fillDislike();
           }
       },
       error: function(xhr, status, error) {
           if (requestloadDislikeData != currentloadDislikeData) {
               return;
           }
           if (attempt < 3) {
               loadDislikeData(attempt + 1);
           } else {
           }
       }
    });
}


let currentgetDynamicJsonContentWithRefresh = 0;
function getDynamicJsonContentWithRefresh(url_address, htmlElement, attempt = 1, errorInHtml = false) {
    let requestgetDynamicJsonContentWithRefresh = ++currentgetDynamicJsonContentWithRefresh;

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetDynamicJsonContentWithRefresh != currentgetDynamicJsonContentWithRefresh) {
               return;
           }
           $(htmlElement).html(data.message);

           if (data.status) {
               getEntryJson();
               loadEntryMenuContent();
               getIndicators();
           }
       },
       error: function(xhr, status, error) {
           if (requestgetDynamicJsonContentWithRefresh != currentgetDynamicJsonContentWithRefresh) {
               return;
           }
           if (attempt < 3) {
               getDynamicJsonContentWithRefresh(url, htmlElement, attempt + 1, errorInHtml);
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content, retry");
               }
           } else {
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content");
               }
           }
       }
    });
}


function getVoteEditForm() {
  getDynamicContent('{% url "rsshistory:entry-vote-form" object.id %}', "#entryVoteContainer", 1, true);
}


function showTagEditForm() {
  getDynamicContent('{% url "rsshistory:entry-tag-form" object.id %}', "#entryTagContainer", 1, true);
}


function loadEntryMenuContent() {
    getDynamicContent("{% url 'rsshistory:get-entry-menu' object.id %}", "#entryMenu", 1, true);
}


function updateEntry() {
    if (entry_json_data == null)
    {
        return;
    }

    tag_string = "";
    entry_json_data.link.tags.forEach(tag => {
        tag_string += `<a href="{% url 'rsshistory:entries' %}?search=tags__tag+%3D%3D+${tag}">#${tag}</a>,`
    });

    tag_string += getEditButton();

    $("#entryTagContainer").html(tag_string);

    if (entry_json_data.link.bookmarked || entry_json_data.link.permanent)
    {
        $('#editTagsButton').show();
    }
    else
    {
        $('#editTagsButton').hide();
    }
}


let currentgetEntryJson = 0;
function getEntryJson(attempt = 1) {
    let requestgetEntryJson = ++currentgetEntryJson;
    let url_address = "{% url 'rsshistory:entry-json' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetEntryJson != currentgetEntryJson) {
               return;
           }
           if (data) {
               entry_json_data = data;
               updateEntry();
           }
       },
       error: function(xhr, status, error) {
           if (requestgetEntryJson != currentgetEntryJson) {
               return;
           }
           if (attempt < 3) {
               getEntryJson(attempt + 1);
           } else {
           }
       }
    });
}


let currententryVote = 0;
function entryVote(attempt = 1) {
    var voteData = $('#id_vote').val();

    let requestentryVote = ++currententryVote;

    $.ajax({
        url: "{% url 'rsshistory:entry-vote' object.id %}",
        type: 'POST',
        timeout: 10000,
        data: {
            vote: voteData,
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        dataType: 'json',
        success: function(response) {
            if (requestentryVote != currententryVote)
            {
                return;
            }

            if (response.status === true) {
                $('#entryVoteContainer').html("Vote added: " + response.vote);
            } else {
                $('#entryVoteContainer').html(`<p class="text-danger">Error: ${response.message}</p>`);
            }
        },
        error: function(xhr, status, error) {
            if (requestentryVote != currententryVote)
            {
                return;
            }

            if (attempt < 3) {
                entryVote(attempt + 1);
            }
            else {
                $('#entryVoteContainer').html(`<p class="text-danger">Error during vote update: ${error}</p>`);
            }
        },
    });
}


let currenttagEntry = 0;
function tagEntry(attempt = 1) {
    var tagsData = $('#id_tag').val();
    const editButton = getEditButton();

    let requesttagEntry = ++currenttagEntry;

    $.ajax({
        url: '{% url "rsshistory:entry-tag" object.id %}',
        type: 'POST',
        timeout: 10000,
        data: {
            tags: tagsData,
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        dataType: 'json',
        success: function(response) {
            if (requesttagEntry != currenttagEntry)
            {
                return;
            }

            getEntryJson();
        },
        error: function(xhr, status, error) {
            if (requesttagEntry != currenttagEntry)
            {
                return;
            }

            if (attempt < 3) {
                tagEntry(attempt + 1);
            }
            else {
                $('#entryTagContainer').html(`<p class="text-danger">Error during tag update. Please try again. ${editButton}</p>`);
            }
        },
    });
}


$(document).on('click', '#Vote', function(event) {
    event.preventDefault();
    getVoteEditForm();
});

$(document).on('click', '#Bookmark', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:entry-bookmark' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Unbookmark', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:entry-unbookmark' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Read-later', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:read-later-add' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Do-not-read-later', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:read-later-remove' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Remove', function(event) {
    event.preventDefault();
    getDynamicJsonContent("{% url 'rsshistory:entry-remove' object.id %}", "#entryStatusLine");
});

$(document).on('submit', '#voteEditForm', function(event) {
    event.preventDefault();

    entryVote();
});

$(document).on('click', '#cancelVoteEdit', function() {
    $('#entryVoteContainer').html("");
});

$(document).on('submit', '#tagEditForm', function(event) {
    event.preventDefault();

    tagEntry();
});

$(document).on('click', '#editTagsButton', function() {
    showTagEditForm();
    $(this).hide();
});

$(document).on('click', '#cancelTagEdit', function() {
    updateEntry();
});


loadEntryDynamicDetails();
loadDislikeData();
fillIsEntryDownloaded();
getEntryJson();


setInterval(function() {
    fillIsEntryDownloaded();
    getEntryJson();
}, 300000);
