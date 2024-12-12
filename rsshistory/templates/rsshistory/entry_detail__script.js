{% load static %}


let entry_json_data = null;
let is_downloading = false;


function getEditButton() {
    return `<button id="editTagsButton"><img src="{% static 'rsshistory/icons/icons8-edit-100.png' %}" class="content-icon" /></button>`;
}


function getDownloadingText() {
    return '<span class="bg-warning text-dark"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Downloading...</span>';
}


let currentIsDownloading = 0;
function fillIsEntryDownloaded(attempt = 1) {
    let requestIsDownloading = ++currentIsDownloading;

    $.ajax({
        url: "{% url 'rsshistory:is-entry-download' object.id %}",
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestIsDownloading != currentIsDownloading) {
                return;
            }
            is_downloading = data.status;

            if (is_downloading) {
                const text = getDownloadingText();
                $('#entryDownloadLine').html(text);
            }
            else {
                $('#entryDownloadLine').html("");
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
    getDynamicContent('{% url "rsshistory:entry-vote-form" object.id %}', "#entryVoteLine", 1, true);
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
                $('#entryStatusLine').html("Vote added: " + response.vote);
                $('#entryVoteLine').html("");
            } else {
                $('#entryStatusLine').html(`<p class="text-danger">Error: ${response.message}</p>`);
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
                $('#entryStatusLine').html(`<p class="text-danger">Error during vote update: ${error}</p>`);
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
    $('#entryVoteLine').html("");
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
fillIsEntryDownloaded(); //TODO maybe this is not necessary. Maybe move it to entry json
getEntryJson();


setInterval(function() {
    fillIsEntryDownloaded();
    getEntryJson();
}, 300000);
