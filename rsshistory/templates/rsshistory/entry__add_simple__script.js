// TODO - make two parallel requests
// one for form, one for data
// when both return, then perform.
// could be faster

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

let submission_locked = true;
let form_text = null;
let page_properties = null;


function getFormattedDate(input_date) {
    let dateObject = input_date ? new Date(input_date) : new Date();

    let formattedDate = dateObject.getFullYear() + "-" +
        String(dateObject.getMonth() + 1).padStart(2, "0") + "-" +
        String(dateObject.getDate()).padStart(2, "0") + " " +
        String(dateObject.getHours()).padStart(2, "0") + ":" +
        String(dateObject.getMinutes()).padStart(2, "0") + ":" +
        String(dateObject.getSeconds()).padStart(2, "0");

    return formattedDate;
}


function resetSearch(text = '') {
    $('#btnFetch').prop("disabled", false);
    $('#btnFetch').html("Submit")
    if (text) {
        $("#formResponse").html(text);
    }
}


function fillEditForm(properties, token) {
    if (properties[0].name != "Properties") {
        console.error("Incorrect name 0");
        console.error(properties[0].name);
        return;
    }
    if (properties[1].name != "Contents") {
        console.error("Incorrect name 1");
        console.error(properties[1].name);
        return;
    }
    if (properties[2].name != "Options") {
        console.error("Incorrect name 1");
        console.error(properties[1].name);
        return;
    }
    if (properties[3].name != "Response") {
        console.error("Incorrect name 2");
        console.error(properties[2].name);
        return;
    }

    let link = properties[0].data.link;
    let title = properties[0].data.title || '';
    let description = properties[0].data.description || '';
    let date_published = properties[0].data.date_published;
    let source_url = "";
    let bookmarked = true;
    let permanent = false;
    let language = properties[0].data.language || '';
    let user = properties[0].data.user;
    let author = properties[0].data.author || '';
    let album = properties[0].data.album || '';
    let thumbnail = properties[0].data.thumbnail || '';
    let manual_status_code = 0;
    let status_code = properties[3].data.status_code;
    let page_rating = properties[0].data.page_rating;
    let page_rating_contents = properties[0].data.page_rating;
    let page_rating_votes = 0;
    let age = 0;

    // make necessary updates

    if (description.length > 1000) {
        description = description.slice(0, 1000);
    }

    date_published = getFormattedDate(date_published);

    // set

    $("#formResponse").html(form_text);

    $("#id_link").val(link);
    $("#id_title").val(title);
    $("#id_description").val(description);
    $("#id_thumbnail").val(thumbnail);
    $("#id_language").val(language);
    $("#id_author").val(author);
    $("#id_album").val(album);
    $("#id_age").val(age);
    $("#id_status_code").val(status_code);
    $("#id_page_rating_contents").val(page_rating_contents);
    $("#id_page_rating_votes").val(page_rating_votes);
    $("#id_page_rating").val(page_rating);
    $("#id_date_published").val(date_published);

    let action_url = `{% url 'rsshistory:entry-add' %}`;

    $("#theForm").attr({
        method: "POST",
        action: action_url
    });
    $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(token);

    submission_locked = false;
}

let currentGetEditForm = 0;
function getEditForm(page_url, properties, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let url = `{% url 'rsshistory:entry-add-form' %}?link=${page_url}`;
    let requestCurrentGetEditForm = ++currentGetEditForm;
    
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestCurrentGetEditForm != currentGetEditForm)
           {
               return;
           }

           form_text = data;
           form_text = form_text.replace('btnFetch', 'btnAddLink');
           
           // TODO you do not have to hide it.
           // we can use different id_link names here.
           let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
           $("#formDiv").html("");

           fillEditForm(properties, csrfToken);
       },
       error: function(xhr, status, error) {
           if (requestCurrentGetEditForm != currentGetEditForm)
           {
               return;
           }
           
           if (attempt < 3) {
               getEditForm(page_url, properties, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form");
           }
       }
    });
}


function fillData(page_url, properties) {
    let htmlOutput = "";

    if (properties && properties.length > 0) {
        getEditForm(page_url, properties);
    }

    return htmlOutput;
}

let currentPageProperties = 0;
function sendPagePropertiesRequest(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Fetching link properties ${page_url} with browser:${browser}`);
    let url = `{% url 'rsshistory:get-page-properties' %}?page=${page_url}&browser=${browser}`;

    const requestCurrentPageProperties = ++currentPageProperties;

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 40000,  // this depends on configuration
       success: function(data) {
           if (requestCurrentPageProperties != currentPageProperties)
               return;
           
           if (data.status) {
               let text = fillData(page_url, data.properties);
               $("#formResponse").html(text);
               $('#btnFetch').prop("disabled", false);
               $('#btnFetch').html("Submit");
           }
           else {
               resetSearch("Incorrect call of get page request");
           }
       },
       error: function(xhr, status, error) {
           if (requestCurrentPageProperties != currentPageProperties)
               return;
               
           if (attempt < 3) {
               $("#formResponse").html("Could not obtain page properties. Retry");
               getPageProperties(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain page properties.");
           }
       }
    });
}

let currentsendJqueryPageProperties = 0;
function sendJqueryPageProperties(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let requestsendJqueryPageProperties = ++currentsendJqueryPageProperties;

    let url = `{% url 'rsshistory:entry-add-form' %}?link=${page_url}`;
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestsendJqueryPageProperties != currentsendJqueryPageProperties)
               return;

           let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
           // $("#formDiv").html("");

           form_text = data;
           form_text = data.replace('btnFetch', 'btnAddLink');

           // TODO - fetch using jQuery for title and other info
           resetSearch("Feature not yet implemented.");

           submission_locked = false;
       },
       error: function(xhr, status, error) {
           if (requestsendJqueryPageProperties != currentsendJqueryPageProperties)
               return;

           if (attempt < 3) {
               sendJqueryPageProperties(page_url, properties, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form.");
           }
       }
    });
}

let currentsendEmptyFrame = 0;
function sendEmptyFrame(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let requestsendEmptyFrame = ++currentsendEmptyFrame;

    let url = `{% url 'rsshistory:entry-add-form' %}?link=${page_url}`;
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestsendEmptyFrame != currentsendEmptyFrame)
               return;
           let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
           $("#formDiv").html("");

           form_text = data;
           form_text = data.replace('btnFetch', 'btnAddLink');

           $("#formResponse").html(form_text);

           $("#id_link").val(page_url);

           let action_url = `{% url 'rsshistory:entry-add' %}`;

           $("#theForm").attr({
               method: "POST",
               action: action_url
           });
           $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(csrfToken);

           submission_locked = false;
       },
       error: function(xhr, status, error) {
           if (requestsendEmptyFrame != currentsendEmptyFrame)
               return;
           if (attempt < 3) {
               sendEmptyFrame(page_url, properties, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form.");
           }
       }
    });
}

function getPageProperties(page_url, browser) {
    if (browser == -1) {
        sendJqueryPageProperties(page_url, browser);
    }
    else if (browser == -2) {
        sendEmptyFrame(page_url, browser);
    }
    else {
        sendPagePropertiesRequest(page_url, browser);
    }
}


function getEntryLink(entry_id) {
    let entry_detail_url = "{% url 'rsshistory:entry-detail' 1017 %}";
    entry_detail_url = entry_detail_url.replace("1017", entry_id);

    entry_link = `<a href="${entry_detail_url}" class="btn btn-secondary">Link to existing entry</a>`;

    return entry_link;
}

let currentcheckEntryExists = 0;
function checkEntryExists(page_url, browser, attempt=1) {
    $("#formResponse").html(`Checking if link exists ${page_url}`);

    let url = `{% url 'rsshistory:entry-is' %}?link=${page_url}`;
    
    let requestCurrentcheckEntryExists = ++currentcheckEntryExists;

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestCurrentcheckEntryExists != currentcheckEntryExists)
           {
               return;
           }
           
           if (data.status) {
               entry_id = data.pk;
               entry_link = getEntryLink(entry_id);

               $("#formResponse").html(`Entry exists ${entry_link}`);
               resetSearch();
           }
           else {
               getPageProperties(page_url, browser);
           }
       },
       error: function(xhr, status, error) {
           if (requestCurrentcheckEntryExists != currentcheckEntryExists)
           {
               return;
           }
           if (attempt < 3) {
               $("#formResponse").html("Could not obtain information. Retry");
               checkEntryExists(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain information if link exists.");
           }
       }
    });
}


function onUserInput() {
   $('#btnFetch').prop("disabled", true);
   
   const page_url = $('#id_link').val();
   const browser = $('#id_browser').val();
   
   checkEntryExists(page_url, browser);
}


$(document).ready(function() {
   $("#btnFetch").click(function(event) {
       event.preventDefault();
   
       onUserInput();
   });
});

$(document).on('submit', '#theForm', function(event) {
    if (submission_locked) {
        event.preventDefault();
    }
});

$("#btnAddLink").click(function(event) {
   event.preventDefault();
   putSpinnerOnIt($(this));
});

$('#theForm input[name="link"]').on('input', function() {
    var link = $('#theForm input[name="link"]').val();

    // TODO display errors, if ends with /, or if it has # in link, or if
    //
    // can we decode stupid google links?

    //if (link.endswith) {
    //}
});
