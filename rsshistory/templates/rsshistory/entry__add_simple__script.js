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


function getExistingObjectLink(object_id) {
    let detail_url = "{% url 'rsshistory:entry-detail' 1017 %}";
    detail_url = detail_url.replace("1017", object_id);

    link_text = `<a href="${detail_url}" class="btn btn-secondary">Link to existing object</a>`;

    return link_text;
}


let currentaddLink = 0;
function addLink(page_url) {
    let url = `{% url 'rsshistory:entry-add-json' %}?link=${page_url}`;
    
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

               $("#formResponse").html(`Entry exists ${link_text}`);
               resetSearch();
           }
           else {
               object_id = data.pk;
               link_text = getExistingObjectLink(object_id);
               $("#formResponse").html(`Entry added ${link_text}`);
           }
       },
       error: function(xhr, status, error) {
           if (requestaddLink != currentaddLink)
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
               addLink(page_url);
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
