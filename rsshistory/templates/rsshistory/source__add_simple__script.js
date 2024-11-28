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


function resetSearch(text = '') {
    $('#btnFetch').prop("disabled", false);
    $('#btnFetch').html("Submit")
    if (text) {
        $("#formResponse").html(text);
    }
}


function fillEditForm(token) {
    $("#formResponse").html(form_text);

    let action_url = `{% url 'rsshistory:source-add' %}`;

    $("#theForm").attr({
        method: "POST",
        action: action_url
    });
    $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(token);

    submission_locked = false;
}


let currentGetEditForm = 0;
function getRealEditForm(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let url = `{% url 'rsshistory:source-add-form' %}?link=${page_url}`;
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

           fillEditForm(csrfToken);
       },
       error: function(xhr, status, error) {
           if (requestCurrentGetEditForm != currentGetEditForm)
           {
               return;
           }
           
           if (attempt < 3) {
               getRealEditForm(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form");
           }
       }
    });
}


let currentsendJqueryPageProperties = 0;
function sendJqueryPageProperties(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let requestsendJqueryPageProperties = ++currentsendJqueryPageProperties;

    let url = `{% url 'rsshistory:source-add-form' %}?link=${page_url}`;
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
               sendJqueryPageProperties(page_url, browser, attempt + 1);
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

    let url = `{% url 'rsshistory:source-add-form' %}?link=${page_url}`;
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

           let action_url = `{% url 'rsshistory:source-add' %}`;

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
               sendEmptyFrame(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form.");
           }
       }
    });
}

function getForm(page_url, browser) {
    if (browser == -1) {
        sendJqueryPageProperties(page_url, browser);
    }
    else if (browser == -2) {
        sendEmptyFrame(page_url, browser);
    }
    else {
        getRealEditForm(page_url, browser);
    }
}


function getExistingObjectLink(object_id) {
    let detail_url = "{% url 'rsshistory:source-detail' 1017 %}";
    detail_url = detail_url.replace("1017", object_id);

    link_text = `<a href="${detail_url}" class="btn btn-secondary">Link to existing object</a>`;

    return link_text;
}


let currentcheckEntryExists = 0;
function checkEntryExists(page_url, browser, attempt=1) {
    $("#formResponse").html(`Checking if link exists ${page_url}`);

    let url = `{% url 'rsshistory:source-is' %}?link=${page_url}`;
    
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
               object_id = data.pk;
               detail_link_text = getExistingObjectLink(object_id);

               $("#formResponse").html(`Object exists ${detail_link_text}`);
               resetSearch();
           }
           else {
               getForm(page_url, browser);
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
