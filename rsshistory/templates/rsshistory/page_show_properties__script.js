{% load static %}


let page_properties = null;


function getCollapsedPropertyItem(name, data) {
    htmlOutput = `
    <a class="btn btn-secondary" data-bs-toggle="collapse" href="#collapse${name}" role="button" aria-expanded="false" aria-controls="collapse${name}">
        Show Details
    </a>
    <div class="collapse" id="collapse${name}"><pre>${data}</pre></div>`;

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
    else if (property.name == "Headers") {
        let contents = property.data.Headers;
        let escapedHeaders = escapeHtml(contents);

        htmlOutput += getCollapsedPropertyItem("Headers", escapedHeaders);
    }
    else {
        for (const [key, value] of Object.entries(property.data)) {
            htmlOutput += `
                <div>
                    <strong>${key}:</strong> ${value ?? "N/A"}
                </div>
            `;
        }
    }

    return htmlOutput;
}


function fillData() {
    let htmlOutput = "";

    if (page_properties && page_properties.length > 0) {
        page_properties.forEach(property => {
            htmlOutput += fillDataProperty(property);
        });
    }

    return htmlOutput;
}


let currentgetPageProperties = 0;
function getPageProperties(page_url, browser, attempt = 1) {
    let requestgetPageProperties = ++currentgetPageProperties;

    let encodedPageUrl = encodeURIComponent(page_url);
    let url = `{% url 'rsshistory:get-page-properties' %}?link=${encodedPageUrl}&browser=${browser}`;

    let spinner_text = getSpinnerText(`Fetching... ${url}`);
    $("#propertiesResponse").html(spinner_text);

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
           let text = fillData(data.properties);
           $("#propertiesResponse").html(text);
           $('.btnFilterTrigger').prop("disabled", false);
           $('.btnFilterTrigger').html("Submit")
       },
       error: function(xhr, status, error) {
           if (requestgetPageProperties != currentgetPageProperties)
           {
               return;
           }
           if (attempt < 3) {
               $("#propertiesResponse").html("Could not obtain information. Retry");
               getPageProperties(page_url, browser, attempt + 1);
           } else {
               $("#propertiesResponse").html("Could not obtain information. Error");
               $('.btnFilterTrigger').prop("disabled", false);
               $('.btnFilterTrigger').html("Submit")
           }
       }
    });
}


function OnUserInput() {
    $('.btnFilterTrigger').prop("disabled", true);

    const link = $('#id_link').val();
    const browser = $('#id_browser').val();

    if (link == null) {
        return;
    }

    getPageProperties(link, browser);
}


$(document).ready(function() {
    $("#btnFetch").click(function(event) {
        event.preventDefault();

        OnUserInput();
    });

    if (getQueryParam("link") != null) {
        OnUserInput();
    }
});


$(document).on('submit', '#theForm', function(event) {
    event.preventDefault();
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
