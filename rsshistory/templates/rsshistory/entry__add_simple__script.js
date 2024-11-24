// TODO - make two parallel requests
// one for form, one for data
// when both return, then perform.
// could be faster

function escapeHtml(unsafe)
{
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

let submission_locked = true;


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


function fillEditForm(properties, form_text, token) {
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

    let action_url = `{% url 'rsshistory:entry-add' %}`;

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

    form_text = form_text.replace('btnFetch', 'btnAddLink');

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

    $("#theForm").attr({
        method: "POST",
        action: action_url
    });
    $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(token);

    submission_locked = false;
}

let currentGetEditForm = 0;
function getEditForm(link, properties, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${link}`);

    let url = `{% url 'rsshistory:entry-add-form' %}?link=${link}`;
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
           
           // TODO you do not have to hide it.
           // we can use different id_link names here.
           let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
           $("#formDiv").html("");

           fillEditForm(properties, data, csrfToken);
       },
       error: function(xhr, status, error) {
           if (requestCurrentGetEditForm != currentGetEditForm)
           {
               return;
           }
           
           if (attempt < 3) {
               getEditForm(link, properties, attempt + 1);
           } else {
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
       timeout: 10000,
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
               $("#formResponse").html("Incorrect call of get page request");
           }
       },
       error: function(xhr, status, error) {
           if (requestCurrentPageProperties != currentPageProperties)
               return;
               
           if (attempt < 3) {
               $("#formResponse").html("Could not obtain information. Retry");
               getPageProperties(page_url, browser, attempt + 1);
           } else {
             $("#formResponse").html("Could not obtain information. Error");
             $('#btnFetch').prop("disabled", false);
             $('#btnFetch').html("Submit")
           }
       }
    });
}

function sendJqueryPageProperties(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${link}`);

    let url = `{% url 'rsshistory:entry-add-form' %}?link=${link}`;
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
           $("#formDiv").html("");

           // TODO - fetch using jQuery for title and other info

           form_text = data.replace('btnFetch', 'btnAddLink');

           $("#formResponse").html(form_text);

           $("#theForm").attr({
               method: "POST",
               action: action_url
           });
           $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(token);

           submission_locked = false;
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               sendJqueryPageProperties(page_url, properties, attempt + 1);
           } else {
           }
       }
    });
}

function getPageProperties(page_url, browser) {
    if (browser == -1) {
        sendJqueryPageProperties(page_url, browser);
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
function checkEntryExists(link, browser, attempt=1) {
    $("#formResponse").html(`Checking if link exists ${link}`);

    let url = `{% url 'rsshistory:entry-is' %}?link=${link}`;
    
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
               $('#btnFetch').prop("disabled", false);
               $('#btnFetch').html("Submit")
           }
           else {
               getPageProperties(link, browser);
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
             $("#formResponse").html("Could not obtain information. Error");
             $('#btnFetch').prop("disabled", false);
             $('#btnFetch').html("Submit")
           }
       }
    });
}


function onUserInput() {
   $('#btnFetch').prop("disabled", true);
   
   const link = $('#id_link').val();
   const browser = $('#id_browser').val();
   
   checkEntryExists(link, browser);
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
