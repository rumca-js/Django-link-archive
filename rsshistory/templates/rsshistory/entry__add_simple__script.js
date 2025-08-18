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


let currentaddLink = 0;
function addLink(page_url, browser, attempt=1) {
    let url = `{% url 'rsshistory:entry-add-json' %}?link=${page_url}&browser=${browser}`;
    
    let requestaddLink = ++currentaddLink;

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestaddLink != currentaddLink)
           {
               return;
           }
           
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
       },
       error: function(xhr, status, error) {
           if (requestaddLink != currentaddLink)
           {
               return;
           }
           if (attempt < 3) {
               addLink(page_url, browser, attempt + 1);
           } else {
               resetSearch();
           }
       }
    });
}


let currentcheckEntryExists = 0;
function checkEntryExistsAndAdd(page_url, browser, attempt=1) {
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

               $("#Errors").html(`Entry exists ${link_text}`);
               resetSearch();
           }
           else {
               addLink(page_url);
           }
       },
       error: function(xhr, status, error) {
           if (requestCurrentcheckEntryExists != currentcheckEntryExists)
           {
               return;
           }
           if (attempt < 3) {
               $("#Errors").html("Could not obtain information. Retry");
               checkEntryExistsAndAdd(page_url, browser, attempt + 1);
           } else {
               resetSearch("Could not obtain information if link exists.");
           }
       }
    });
}


function onUserInput() {
   const page_url = $('#id_link').val();
   const browser = $('#id_browser').val();

   $('#Errors').html("")
   $('#formResponse').html("")

   if (page_url == null)
   {
       return;
   }

   $('#btnFetch').prop("disabled", true);
   
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


function checkEntryExistsInDb(search_link) {
    let entryCheckUrl = `{% url 'rsshistory:entry-is' %}?link=${encodeURIComponent(search_link)}`;

    fetch(entryCheckUrl)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(entryData => {
            console.log('Entry check data:', entryData);

            if (entryData.status) {
                $('#btnFetch').prop("disabled", true);

		let archived = entryData.archived;

                let link_text = getExistingObjectLink(entryData.pk, archived);
                $('#Errors').append(`<div>The entry already exists ${link_text}.</div>`);
            }
            else {
                $('#btnFetch').prop("disabled", false);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
}


function fetchLinkSuggestions(search_link) {
    let url = `{% url 'rsshistory:link-input-suggestions-json' %}?link=${encodeURIComponent(search_link)}`;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log('Fetched data:', data);

            if (data.status && Array.isArray(data.links) && data.links.length > 0) {
                $('#Suggestions').append(`<div>Other link suggestions</div>`);
                data.links.forEach(link => {
                    $('#Suggestions').append(`<button class="suggestion-link btn btn-secondary d-block">${link}</button>`);
                });
            }

            if (data.status && Array.isArray(data.errors) && data.errors.length > 0) {
                $('#Errors').append(`<h2>Errors</h2>`);
                data.errors.forEach(error => {
                    $('#Errors').append(`<div>${error}</div>`);
                });
	    }
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
}
