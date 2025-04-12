// TODO - make two parallel requests
// we do not have to ping for form every time. we could be requesting it once, then only
// replace it with new properties


let submission_locked = true;
let form_text = null;
let page_properties = null;
const EMPTY_FORM = -1;
const AUTO = -2;


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


function getSection(section_name) {
    if (page_properties && page_properties.length > 0) {
        let section = page_properties.find(properties => properties.name == section_name);
        return section ? section.data : null;
    }
    return null;
}


function fillEditForm(token) {
    let page_properties = getSection("Properties");
    let response_data = getSection("Response");

    let link = page_properties.link;
    let title = page_properties.title || '';
    let description = page_properties.description || '';
    let date_published = page_properties.date_published;
    let source_url = "";
    let bookmarked = true;
    let permanent = false;
    let language = page_properties.language || '';
    let user = page_properties.user;
    let author = page_properties.author || '';
    let album = page_properties.album || '';
    let thumbnail = page_properties.thumbnail || '';
    let manual_status_code = 0;
    let status_code = response_data.status_code;
    let page_rating = page_properties.page_rating;
    let page_rating_contents = page_properties.page_rating;
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
function getEditForm(page_url, attempt = 1) {
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

           fillEditForm(csrfToken);
       },
       error: function(xhr, status, error) {
           if (requestCurrentGetEditForm != currentGetEditForm)
           {
               return;
           }
           
           if (attempt < 3) {
               getEditForm(page_url, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form");
           }
       }
    });
}


function fillData(page_url) {
    let htmlOutput = "";

    if (page_properties && page_properties.length > 0) {
        getEditForm(page_url);
    }

    return htmlOutput;
}


let currentPageProperties = 0;
function sendPagePropertiesRequest(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Fetching link properties ${page_url} with browser:${browser}`);

    let encodedPageUrl = encodeURIComponent(page_url);

    let url = `{% url 'rsshistory:get-page-properties' %}?link=${encodedPageUrl}&browser=${browser}`;

    const requestCurrentPageProperties = ++currentPageProperties;

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 40000,  // this depends on configuration
       success: function(data) {
           if (requestCurrentPageProperties != currentPageProperties)
               return;
           
           if (data.status) {
               page_properties = data.properties;

               let text = fillData(page_url);
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
               sendEmptyFrame(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain edit form.");
           }
       }
    });
}


function getPageProperties(page_url, browser) {
    if (browser == EMPTY_FORM) {
        sendEmptyFrame(page_url, browser);
    }
    else {
        sendPagePropertiesRequest(page_url, browser);
    }
}


function getExistingObjectLink(object_id) {
    let detail_url = "{% url 'rsshistory:entry-detail' 1017 %}";
    detail_url = detail_url.replace("1017", object_id);

    link_text = `<a href="${detail_url}" class="btn btn-secondary">Link to existing object</a>`;

    return link_text;
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
               object_id = data.pk;
               link_text = getExistingObjectLink(object_id);

               $("#formResponse").html(`Entry exists ${link_text}`);
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
   const page_url = $('#id_link').val();
   const browser = $('#id_browser').val();

   if (page_url == null)
   {
       return;
   }

   $('#btnFetch').prop("disabled", true);
   
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
    let element = $('#theForm input[name="link"]');

    var search_link = element.val();
    new_search_link = fixStupidGoogleRedirects(search_link);
    if (new_search_link && search_link != new_search_link)
    {
        element.val(new_search_link);
    }
});
