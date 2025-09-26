// TODO - make two parallel requests
// we do not have to ping for form every time. we could be requesting it once, then only
// replace it with new properties


let submission_locked = true;
let form_text = null;
let page_properties = null;
const EMPTY_FORM = -1;
const AUTO = -2;


function addError(error) {
    $('#Errors').append(`<div class="alert alert-danger">${error}</div>`);
}


function resetSearch(text = '') {
    $('.btnFilterTrigger').prop("disabled", false);
    $('#btnFetch').html("Submit")
    if (text) {
        $("#Errors").html(text);
    }
}


function getExistingObjectLink(object_id, archive=false) {
    let detail_url = "";
    if (archive) {
       detail_url = "{% url 'rsshistory:entry-archived' 1017 %}";
    }
    else
    {
       detail_url = "{% url 'rsshistory:entry-detail' 1017 %}";
    }
    detail_url = detail_url.replace("1017", object_id);

    if (detail_url == "")
    {
       return "";
    }

    link_text = `<a href="${detail_url}" class="btn btn-secondary">Entry</a>`;

    return link_text;
}


function addLink(page_url, browser, attempt=1) {
    addEntryJson(page_url, browser, function(data) {
      if (data.status) {
          object_id = data.pk;
          link_text = getExistingObjectLink(object_id);

          $("#formResponse").html(`Entry added ${link_text}`);
          $('#Errors').html("")
          $('#Suggestions').html("")

          resetSearch();
      }
      else {
          object_id = data.pk;
          link_text = getExistingObjectLink(object_id);
          $("#formResponse").html(`Entry not added`);
      }
      resetSearch();
    });
}


function checkEntryExistsAndAdd(page_url, browser, attempt=1) {
    $("#formResponse").html(`Checking if link exists ${page_url}`);

    isEntry(page_url, function(data) {
       if (data.status) {
           object_id = data.pk;
           link_text = getExistingObjectLink(object_id);

           addError(`Entry already exists ${link_text}`);
           resetSearch();
       }
       else {
           addLink(page_url);
       }
    });
}


function checkEntryExistsInDb(page_url) {
    $("#formResponse").html(`Checking if entry exists ${page_url}`);

    isEntry(page_url, function(entryData) {
        console.log('Entry check data:', entryData);

        if (entryData.status) {
             $('.btnFilterTrigger').prop("disabled", true);

             let archived = entryData.archived;

             let link_text = getExistingObjectLink(entryData.pk, archived);
             addError(`Entry already exists ${link_text}`);
        }
        else {
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
    getLinkInputSuggestionsJson(page_url, function(data) {
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
    
    addLink(page_url, browser);
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

       checkEntryExistsInDb(search_link);
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


$(document).on('click', '.suggestion-link', function(event) {
    event.preventDefault();
    let element = $('#theForm input[name="link"]');
    let text = $(this).text();
    console.log(`Clicked on element ${text}`);
    element.val(text);

    onInputChanged();
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
