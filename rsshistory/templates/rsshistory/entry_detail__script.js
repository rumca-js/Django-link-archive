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


function getEntryMenu() {
    getDynamicJson("{% url 'rsshistory:json-entry-menu' object.id %}", function(data) {
        let text = getMenuEntries(data.menu);

        $("#entryMenu").html(text);
    });
}


function fillEntryStatus() {
    if (is_updating || is_resetting) {
        const text = getDownloadingText("Fetching link data...");
        $('#entryUpdateContainer').html(text);

    }
    else {
        $('#entryUpdateContainer').html("");
    }
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

            fillEntryStatus();
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
function getThisEntryOperationalParameters(attempt = 1) {
    getEntryOperationalParamters({{object.id}}, function (data) {
        let html_out = "";

        if (data) {
          if (data.status) {
              data.parameters.forEach(parameter => {
                  let title = parameter.title || parameter.name;
                  let name = escapeHtml(parameter.name);
                  let description = escapeHtml(parameter.description);

                  html_out += `<div class="text-nowrap mx-1"
                      title="${title}"
                      >
                         <strong>${name}:</strong>
                         ${description}
                      </div>`;
              });

              if (html_out) {
                  html_out = "<h1>Parameters</h1>" + html_out;
              }

              $("#entryOperationalParameters").html(html_out);
          }
        }
    });
}


function fillEntryParameters() {
   console.log(`fillEntryParameters ${entry_json_data} ${entry_dislike_data}`);

   console.log("entry parameters 0");
   if (entry_json_data == null)
   {
       console.log("entry parameters 1");
       return;
   }
   console.log("entry parameters 2");
   let entry = entry_json_data.link;

   let parameters = getEntryParameters(entry, entry_dislike_data);
   $('#entryParameters').html(parameters);
}


function getThisEntryDislikeData(attempt = 1) {
   getEntryDislikeData({{object.id}}, function (data) {
       if (data) {
           entry_dislike_data = data;
           fillEntryParameters();
       }
   });
}


const getDynamicJsonContentWithRefreshTracker = {};
function getDynamicJsonContentWithRefresh(url_address, htmlElement, errorInHtml = false) {
    if (!getDynamicJsonContentWithRefreshTracker[url_address]) {
        getDynamicJsonContentWithRefreshTracker[url_address] = 0;
    }
    const requestId = ++getDynamicJsonContentWithRefreshTracker[url_address];

    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           //if (getDynamicContentRequestTracker[url_address] !== requestId) {
           //    return;
           //}
           $(htmlElement).html(data.message);

           if (data.status) {
               getEntryProperties();
               getEntryMenu();
               getIndicators();
	       getIsEntryDownloaded();
           }
       },
       error: function(xhr, status, error) {
           //if (getDynamicContentRequestTracker[url_address] !== requestId) {
           //    return;
           //}
           //getDynamicJsonContentWithRefresh(url_address, htmlElement, errorInHtml);
       }
    });
}


function getVoteEditForm() {
  getDynamicContent('{% url "rsshistory:entry-vote-form" object.id %}', "#entryVoteContainer");
}


function getTagEditForm() {
  getDynamicContent('{% url "rsshistory:entry-tag-form" object.id %}', "#entryTagContainer");
}


function getEntryTagLink(tag) {
    if (tag) {
       return `<a href="{% url 'rsshistory:entries' %}?search=tags__tag+%3D%3D+${tag}">#${tag}</a>,`
    }
    return "";
}


function updateEntryProperties() {
    console.log(`updateEntryProperties ${entry_json_data} ${entry_dislike_data}`);
    if (entry_json_data == null)
    {
        return;
    }

    let entry = entry_json_data.link;

    let tag_string = getEntryDetailTags(entry);

    tag_string += getEditButton();
    $("#entryTagContainer").html(tag_string);

    $("#entryTitle").html(entry.title);
    $("#entryDescription").html(getEntryDescription(entry));
    $("#entryLanguage").html(entry.language);
    $("#entryAuthor").html(entry.author);
    $("#entryAlbum").html(entry.album);
    $("#entryAge").html(entry.age);
    $("#entryDatePublished").html(getEntryDate(entry.date_published));
    $("#entryDateCreated").html(getEntryDate(entry.date_created));
    $("#entryDateUpdateLast").html(getEntryDate(entry.date_update_last));
    $("#entryDateModified").html(getEntryDate(entry.date_last_modified));
    $("#entryDateDeadSince").html(getEntryDate(entry.date_dead_since));
    $("#entryStatusCode").html(entry.status_code);
    $("#entryManualStatusCode").html(entry.manual_status_code);
    $("#entryPageRatingVisits").html(entry.page_rating_visits);
    $("#entryPageRatingVotes").html(entry.page_rating_votes);
    $("#entryPermanent").html(entry.permanent);
    $("#entryBookmarked").html(entry.bookmarked);

    $('#editTagsButton').show();

    fillEntryParameters();
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
            htmlOutput += getEntryRelatedBar(entry, {{object.id}});
        });
    }
    $("#entryRelated").html(htmlOutput);
}


function getEntryRelated() {
    let url_address = "{% url 'rsshistory:entry-related-json' object.id %}";

    getDynamicJson(url_address, function(data) {
        if (data) {
            entry_related_data = data;
            fillEntryRelated();
        }
    });
}

function updateEntry() {
    let url = "{% url 'rsshistory:json-entry-update-data' object.id %}";

    getDynamicJson(url_address, function(data) {
       getIsEntryDownloaded();
       $("#entryStatusLine").html(data.message);
    });
}


let currentgetEntryTags = 0;
function getEntryTags() {
    let requestgetEntryTags = ++currentgetEntryTags;
    let url_address = "{% url 'rsshistory:entry-tags' object.id %}";

    getDynamicJson(url_address, function(data) {
       if (data) {
          if (data.status) {
              let tag_string = getEntryDetailTags(data);
              tag_string += getEditButton();
              $("#entryTagContainer").html(tag_string);
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


{% include "rsshistory/urls.js" %}


$(document).on('click', '#Vote', function(event) {
    event.preventDefault();
    getVoteEditForm();
});

$(document).on('click', '#Bookmark', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-entry-bookmark' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Unbookmark', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-entry-unbookmark' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Update-data', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-entry-update-data' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Reset-data', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-entry-reset-data' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Reset-local-data', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-entry-reset-local-data' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Read-later', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-read-later-add' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Do-not-read-later', function(event) {
    event.preventDefault();
    getDynamicJsonContentWithRefresh("{% url 'rsshistory:json-read-later-remove' object.id %}", '#entryStatusLine');
});

$(document).on('click', '#Remove', function(event) {
    event.preventDefault();
    getDynamicJsonContent("{% url 'rsshistory:json-entry-remove' object.id %}", "#entryStatusLine");
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


getEntryProperties();
getEntryRelated();
getThisEntryOperationalParameters();
getThisEntryDislikeData();
getIsEntryDownloaded();
getEntryTags();
getEntryMenu();
