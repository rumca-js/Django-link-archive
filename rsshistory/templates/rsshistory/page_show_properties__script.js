{% load static %}

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

function fillDataProperty(property) {
    let htmlOutput = "";

    let property_name = property.name;

    htmlOutput += `<h1>${property_name}</h1>`;

    if (property.name == "Contents") {
        let contents = property.data.Contents;
        let escapedContents = escapeHtml(contents);

        htmlOutput += `
        <a class="btn btn-secondary" data-bs-toggle="collapse" href="#collapseContents" role="button" aria-expanded="false" aria-controls="collapseContents">
            Show Details
        </a>
        <div class="collapse" id="collapseContents"><pre>${escapedContents}</pre></div>`;
    }
    else if (property.name == "Headers") {
        let contents = property.data.Headers;
        let escapedHeaders = escapeHtml(contents);

        htmlOutput += `
        <a class="btn btn-secondary" data-bs-toggle="collapse" href="#collapseHeaders" role="button" aria-expanded="false" aria-controls="collapseHeaders">
            Show Details
        </a>
        <div class="collapse" id="collapseHeaders"><pre>${escapedHeaders}</pre></div>`;
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

function fillData(properties) {
    let htmlOutput = "";

    if (properties && properties.length > 0) {
        properties.forEach(property => {
            htmlOutput += fillDataProperty(property);
        });
    }

    return htmlOutput;
}

function sendRequest(page_url, browser, attempt = 1) {
    let url = `{% url 'rsshistory:get-page-properties' %}?page=${page_url}&browser=${browser}`;
    let spinner_text = getSpinnerText(`Fetching... ${url}`);
    $("#propertiesResponse").html(spinner_text);

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 40000, // TODO this depends on configuration
       success: function(data) {
           let text = fillData(data.properties);
           $("#propertiesResponse").html(text);
           $('.btnFilterTrigger').prop("disabled", false);
           $('.btnFilterTrigger').html("Submit")
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               $("#propertiesResponse").html("Could not obtain information. Retry");
               sendRequest(page_url, browser, attempt + 1);
           } else {
               $("#propertiesResponse").html("Could not obtain information. Error");
               $('.btnFilterTrigger').prop("disabled", false);
               $('.btnFilterTrigger').html("Submit")
           }
       }
    });
}


$(document).ready(function() {
    $("#btnFetch").click(function(event) {
        event.preventDefault();

        $('.btnFilterTrigger').prop("disabled", true);

        const link = $('#id_link').val();
        const browser = $('#id_browser').val();

        sendRequest(link, browser);
    });
});

$(document).on('submit', '#theForm', function(event) {
    event.preventDefault();
});
