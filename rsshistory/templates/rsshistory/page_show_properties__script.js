{% load static %}


let page_properties = null;
let page_errors = null;
let page_warnings = null;
let page_notes = null;


function addError(error) {
    $('#Errors').append(`<div class="alert alert-danger">${error}</div>`);
}


function getCollapsedPropertyItem(name, data) {
    htmlOutput = `
    <a class="btn btn-secondary" data-bs-toggle="collapse" href="#collapse${name}" role="button" aria-expanded="false" aria-controls="collapse${name}">
        Show Details
    </a>
    <div class="collapse" id="collapse${name}"><pre>${data}</pre></div>`;

    return htmlOutput;
}


function displayProperty(propertyEntry) {
   let htmlOutput = "";
   for (const [key, value] of Object.entries(propertyEntry)) {
       if (key != "description")
       {
           htmlOutput += `
           <div>
               <strong>${key}:</strong> ${value ?? "N/A"}
           </div>
       `;
       }
   }

   return htmlOutput;
}


function fillDataProperty(property) {
    let htmlOutput = "";

    let property_name = property.name;

    htmlOutput += `<h1>${property_name}</h1>`;

    if (property.name == "Text") {
        let contents = property.data.Contents;
        let escapedContents = escapeHtml(contents);

        htmlOutput += getCollapsedPropertyItem("Contents", escapedContents);
    }
    else if (property.name == "Binary") {
        let contents = property.data.Binary;
        let escapedContents = escapeHtml(contents);

        htmlOutput += getCollapsedPropertyItem("Binary", escapedContents);
    }
    else if (property.name == "Entries") {
        for (const [key, entryObject] of Object.entries(property.data)) {
            htmlOutput += `<h4>${entryObject.title}</h4>`;
            htmlOutput += displayProperty(entryObject);
            htmlOutput += `<hr/>`;
        }
    }
    else {
        for (const [key, value] of Object.entries(property.data)) {
            if (key != "contents")
            {
                if (key == "settings") {
                   let props = displayProperty(value);
                   htmlOutput += `
                   <div>
                     <strong>${key}:</strong> <div class="cotainer">${props}</div>
                   </div>
                   `;
                }
                else {
                   htmlOutput += `
                   <div>
                       <strong>${key}:</strong> ${value ?? "N/A"}
                   </div>
                    `;
                }
            }
        }
    }

    return htmlOutput;
}


function fillData(data) {
    let htmlOutput = "";

    if (page_properties != null && page_properties.length > 0) {
        page_properties.forEach(property => {
            htmlOutput += fillDataProperty(property);
        });
    }

    if (page_errors != null)
    {
        page_errors.forEach(error => {
            htmlOutput += `<div class="alert alert-danger">${error}</div>`
        });
    }

    if (page_warnings != null)
    {
        page_warnings.forEach(warning => {
            htmlOutput += `<div class="alert alert-warning">${warning}</div>`
        });
    }

    return htmlOutput;
}


let currentgetPageProperties = 0;
function getPageProperties(page_url, browser, attempt = 1) {
    let requestgetPageProperties = ++currentgetPageProperties;

    let encodedPageUrl = encodeURIComponent(page_url);
    let url = `{% url 'rsshistory:json-page-properties' %}?link=${encodedPageUrl}&browser=${browser}`;

    let spinner_text = getSpinnerText(`Fetching... ${url}`);
    $("#formResponse").html(spinner_text);

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 40000, // TODO this depends on configuration
       success: function(data) {
           if (requestgetPageProperties != currentgetPageProperties)
           {
               return;
           }

           page_properties = data.properties;
           if (data.errors)
              page_errors = data.errors;
           if (data.warnings)
              page_warnings = data.warnings;
           if (data.notes)
              page_notes = data.notes;

           let text = fillData(data);

           $("#formResponse").html(text);
           $('.btnFilterTrigger').prop("disabled", false);
           $('.btnFilterTrigger').html("Submit")
       },
       error: function(xhr, status, error) {
           if (requestgetPageProperties != currentgetPageProperties)
           {
               return;
           }
           if (attempt < 3) {
               addError("Could not obtain information. Retry");
               getPageProperties(page_url, browser, attempt + 1);
           } else {
               addError("Could not obtain information. Error");
               $('.btnFilterTrigger').prop("disabled", false);
               $('.btnFilterTrigger').html("Submit")
           }
       }
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


let currentfetchLinkSuggestions = 0;
function fetchLinkSuggestions(page_url) {
    let url = `{% url 'rsshistory:link-input-suggestions-json' %}?link=${encodeURIComponent(page_url)}`;
    let requestfetchLinkSuggestions = ++currentfetchLinkSuggestions;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
           if (requestfetchLinkSuggestions != currentfetchLinkSuggestions)
           {
               return;
           }
           fillLinkSuggestions(data);
        })
        .catch(error => {
           if (requestfetchLinkSuggestions != currentfetchLinkSuggestions)
           {
               return;
           }
           console.error('Fetch error:', error);
        });
}


function OnUserInput() {
    const page_url = $('#id_link').val();
    const browser = $('#id_browser').val();

    $('#Errors').html("")
    $('#formResponse').html("")

    if (page_url == null) {
        return;
    }

    $('.btnFilterTrigger').prop("disabled", true);

    getPageProperties(page_url, browser);
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

        OnUserInput();
    });

    let link = getQueryParam("link");
    if (link != null) {
        $('#id_link').val(link);
        OnUserInput();
    }
});


$(document).on('submit', '#theForm', function(event) {
    event.preventDefault();
});


$('#theForm input[name="link"]').on('input', function() {
    onInputChanged();
});
