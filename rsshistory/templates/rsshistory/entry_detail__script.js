{% load static %}


let entry_json_data = null;
let entry_related_data = null;
let entry_dislike_data = null;
let is_downloading = false;
let is_updating = false;
let is_resetting = false;


function getEditButton() {
    return `<button id="editTagsButton"><img src="{% static 'rsshistory/icons/icons8-edit-100.png' %}" class="content-icon" /></button>`;
}


function getDownloadingText(text = "Downloading...") {
    return `<span class="bg-warning text-dark"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></span> ${text}`;
}


function isEntryDownloadingData(data) {
  return (!is_downloading || !is_updating || is_resetting) && (data.is_downloading || data.is_downloading || data.is_resetting);
}


function isEntryDownloadStop(data) {
  return (is_downloading || is_updating || is_resetting) && (!data.is_downloading && !data.is_downloading && !data.is_resetting);
}


let currentIsDownloading = 0;
function getIsEntryDownloaded(attempt = 1) {
    let requestIsDownloading = ++currentIsDownloading;

    $.ajax({
        url: "{% url 'rsshistory:entry-status' object.id %}",
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestIsDownloading != currentIsDownloading) {
                return;
            }

            if (isEntryDownloadingData(data))
            {
                setTimeout(() => getIsEntryDownloaded(), 60000);
            }
            else if (isEntryDownloadStop(data))
            {
                getEntryProperties();
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
            is_resetting = data.is_resetting;

            if (is_updating || is_resetting) {
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
                getIsEntryDownloaded(attempt + 1);
            }
        }
    });
}


let currentEntryOperationalParamters = 0;
function getEntryOperationalParamters(attempt = 1) {
    let requestEntryOperationalParamters = ++currentEntryOperationalParamters;

    $.ajax({
        url: "{% url 'rsshistory:entry-op-parameters' object.id %}",
        type: 'GET',
        timeout: 15000,
        success: function(data) {
            if (requestEntryOperationalParamters != currentEntryOperationalParamters) {
                return;
            }

            let html_out = "";

            data.parameters.forEach(parameter => {
                html_out += `<div class="text-nowrap mx-1"
                    title="${parameter.title}"
                    >
                       <strong>${parameter.name}:</strong>
                       ${parameter.description}
                    </div>`;
            });

            if (html_out) {
		 html_out = "<h1>Parameters</h1>" + html_out;
	    }

 	    $("#entryOperationalParameters").html(html_out);
	}
    });
}


function fillDislike() {
    let parameters = $('#entryParameters').html();

    let { thumbs_up, thumbs_down, view_count, upvote_ratio, upvote_view_ratio } = entry_dislike_data;

    let text = [];

    if (thumbs_up) text.push(`<div class="text-nowrap mx-1">👍${getHumanReadableNumber(thumbs_up)}</div>`);
    if (thumbs_down) text.push(`<div class="text-nowrap mx-1">👎${getHumanReadableNumber(thumbs_down)}</div>`);
    if (view_count) text.push(`<div class="text-nowrap mx-1">👁${getHumanReadableNumber(view_count)}</div>`);

    if (upvote_ratio) text.push(`<div class="text-nowrap mx-1">👍/👎${parseFloat(upvote_ratio).toFixed(2)}</div>`);
    if (upvote_view_ratio) text.push(`<div class="text-nowrap mx-1">👍/👁${parseFloat(upvote_view_ratio).toFixed(2)}</div>`);

    parameters = `${parameters} ${text.join(" ")}`;

    $('#entryParameters').html(parameters);
}


let currentgetDislikeData = 0;
function getDislikeData(attempt = 1) {
    let requestgetDislikeData = ++currentgetDislikeData;
    let url_address = "{% url 'rsshistory:entry-dislikes' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetDislikeData != currentgetDislikeData) {
               return;
           }
           if (data) {
               entry_dislike_data = data;
               fillDislike();
           }
       },
       error: function(xhr, status, error) {
           if (requestgetDislikeData != currentgetDislikeData) {
               return;
           }
           if (attempt < 3) {
               getDislikeData(attempt + 1);
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
               getEntryProperties();
               getEntryMenuContent();
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


function getTagEditForm() {
  getDynamicContent('{% url "rsshistory:entry-tag-form" object.id %}', "#entryTagContainer", 1, true);
}


function getEntryMenuContent() {
    getDynamicContent("{% url 'rsshistory:get-entry-menu' object.id %}", "#entryMenu", 1, true);
}


function updateEntryProperties() {
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

    $("#entryTitle").html(entry_json_data.title);
    $("#entryDescription").html(entry_json_data.description);
    $("#entryLanguage").html(entry_json_data.language);
    $("#entryAuthor").html(entry_json_data.author);
    $("#entryAlbum").html(entry_json_data.album);
    $("#entryAge").html(entry_json_data.age);
    $("#entryDatePublished").html(entry_json_data.date_published);
    $("#entryDateCreated").html(entry_json_data.date_created);
    $("#entryDateUpdateLast").html(entry_json_data.date_update_last);
    $("#entryDateModified").html(entry_json_data.date_last_modified);
    $("#entryDateDeadSince").html(entry_json_data.date_dead_since);
    $("#entryStatusCode").html(entry_json_data.status_code);
    $("#entryManualStatusCode").html(entry_json_data.manual_status_code);
    $("#entryPageRatingVisits").html(entry_json_data.page_rating_visits);
    $("#entryPageRatingVotes").html(entry_json_data.page_rating_votes);
    $("#entryPermanent").html(entry_json_data.permanent);
    $("#entryBookmarked").html(entry_json_data.bookmarked);

    $('#editTagsButton').show();
}


let currentgetEntryProperties = 0;
function getEntryProperties(attempt = 1) {
    let requestgetEntryProperties = ++currentgetEntryProperties;
    let url_address = "{% url 'rsshistory:entry-json' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetEntryProperties != currentgetEntryProperties) {
               return;
           }
           if (data) {
               entry_json_data = data;
               updateEntryProperties();
           }
       },
       error: function(xhr, status, error) {
           if (requestgetEntryProperties != currentgetEntryProperties) {
               return;
           }
           if (attempt < 3) {
               getEntryProperties(attempt + 1);
           } else {
           }
       }
    });
}


function fillEntryRelated() {
    let htmlOutput = "";

    let entries = entry_related_data.entries;

    if (entries && entries.length > 0) {
        htmlOutput = "<h1>Related</h1>";

        entries.forEach(entry => {
            htmlOutput += getEntryRelatedBar(entry);
        });
    }
    $("#entryRelated").html(htmlOutput);
}


let currentgetEntryRelated = 0;
function getEntryRelated(attempt = 1) {
    let requestgetEntryRelated = ++currentgetEntryRelated;
    let url_address = "{% url 'rsshistory:entry-related-json' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetEntryRelated != currentgetEntryRelated) {
               return;
           }
           if (data) {
               entry_related_data = data;
               fillEntryRelated();
           }
       },
       error: function(xhr, status, error) {
           if (requestgetEntryRelated != currentgetEntryRelated) {
               return;
           }
           if (attempt < 3) {
               getEntryRelated(attempt + 1);
           } else {
           }
       }
    });
}


let currentgetEntryTags = 0;
function getEntryTags(attempt = 1) {
    let requestgetEntryTags = ++currentgetEntryTags;
    let url_address = "{% url 'rsshistory:entry-tags' object.id %}";

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestgetEntryTags != currentgetEntryTags) {
               return;
           }
           if (data) {
               let tag_string = "";
               data.tags.forEach(tag => {
           	  tag_string += `<a href="{% url 'rsshistory:entries' %}?search=tags__tag+%3D%3D+${tag}">#${tag}</a>,`
               });
           
               tag_string += getEditButton();
               $("#entryTagContainer").html(tag_string);
           }
       },
       error: function(xhr, status, error) {
           if (requestgetEntryTags != currentgetEntryTags) {
               return;
           }
           if (attempt < 3) {
               getEntryTags(attempt + 1);
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

            getEntryProperties();
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
    getTagEditForm();
    $(this).hide();
});

$(document).on('click', '#cancelTagEdit', function() {
    getEntryTags();
});


getEntryRelated();
getEntryOperationalParamters();
getDislikeData();
getIsEntryDownloaded();
getEntryTags();
