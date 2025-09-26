// TODO - make two parallel requests
// one for form, one for data
// when both return, then perform.
// could be faster


let submission_locked = true;
let form_text = null;
let url_exists = false;


function addError(error) {
    $('#Errors').append(`<div class="alert alert-danger">${error}</div>`);
}


function resetSearch(text = '') {
    $('.btnFilterTrigger').prop("disabled", false);
    $('#btnFetch').html("Submit")
    if (text) {
        $("#formResponse").html(text);
    }
}


function fillEditForm(token) {
    $("#formDiv").html(form_text);
    $("#formDiv").removeAttr("style")

    let action_url = `{% url 'rsshistory:source-add' %}`;

    $("#theForm").attr({
        method: "POST",
        action: action_url
    });
    $("#theForm").find('input[name="csrfmiddlewaretoken"]').val(token);

    submission_locked = false;
}


function getRealEditForm(page_url, browser, attempt = 1) {
    $("#formResponse").html(`Obtaining form for link :${page_url}`);

    let url = `{% url 'rsshistory:source-add-form' %}?link=${page_url}&browser=${browser}`;

    getSourceAddForm(page_url, browser, function(data) {
        form_text = data;
        form_text = form_text.replace('btnFetch', 'btnAddLink');
           
        // TODO you do not have to hide it.
        // we can use different id_link names here.
        let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        fillEditForm(csrfToken);

        $('#Errors').html("")
        $('#Suggestions').html("")
        $('#formResponse').html("")
    });
}


function getForm(page_url, browser) {
    getRealEditForm(page_url, browser);
}


function getExistingObjectLink(object_id) {
    let detail_url = "{% url 'rsshistory:source-detail' 1017 %}";
    detail_url = detail_url.replace("1017", object_id);

    link_text = `<a href="${detail_url}" class="btn btn-secondary">Source</a>`;

    return link_text;
}


let currentcheckEntryExists = 0;
function checkEntryExists(page_url, browser, attempt=1) {
    $("#formResponse").html(`Checking if source exists ${page_url}`);

    isSource(page_url, function(data) {
       if (data.status) {
           $('.btnFilterTrigger').prop("disabled", true);

           object_id = data.pk;
           detail_link_text = getExistingObjectLink(object_id);

           addError(`Source alredy exists ${detail_link_text}`);
           url_exists = true;
       }
       else {
           url_exists = false;
           $('.btnFilterTrigger').prop("disabled", false);
       }

       $("#formResponse").html("");
    });
}


function fillLinkSuggestions(data) {
    console.log('Fetched data:', data);

    if (data.status && Array.isArray(data.links) && data.links.length > 0) {
         $('#Suggestions').append(`<div>Link suggestions</div>`);
         data.links.forEach(link => {
              $('#Suggestions').append(`<button class="suggestion-link btn btn-secondary d-block">${link}</button>`);
         });
    }

    if (data.status && Array.isArray(data.errors) && data.errors.length > 0) {
       data.errors.forEach(error => {
            addError(`${error}`);
       });
    }
}


function fetchLinkSuggestions(page_url) {
    getSourceInputSuggestionsJson(page_url, function(data) {
        fillLinkSuggestions(data);
    });
}


function onUserInput() {
    const page_url = $('#id_link').val();
    const browser = $('#id_browser').val();

    $('#Errors').html("")
    $('#formResponse').html("")

    if (page_url == null) {
        return;
    }

    $('.btnFilterTrigger').prop("disabled", true);

    getForm(page_url, browser);
}


function onInputChanged() {
    let element = $('#theForm input[name="link"]');
    let search_link = element.val();

    if (search_link) {
       let new_search_link = sanitizeLink(search_link);

       if (new_search_link != search_link) {
          element.val(new_search_link);
          search_link = new_search_link;
       }

       $('#Errors').html("")
       $('#Suggestions').html("")
       $('#formResponse').html("")

       checkEntryExists(search_link);
       fetchLinkSuggestions(search_link);
    }
    else {
       $('#Errors').html("")
       $('#Suggestions').html("")
       $('#formResponse').html("")
    }
}


{% include "rsshistory/urls.js" %}


$(document).ready(function() {
    $("#btnFetch").click(function(event) {
        event.preventDefault();
   
        onUserInput();
    });

    let link = getQueryParam("link");
    if (link != null) {
        $('#id_link').val(link);
        OnUserInput();
    }
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
    onInputChanged();
});


$(document).on('click', '.suggestion-link', function(event) {
    event.preventDefault();
    let element = $('#theForm input[name="link"]');
    let text = $(this).text();
    console.log(`Clicked on element ${text}`);
    element.val(text);

    onInputChanged();
});
