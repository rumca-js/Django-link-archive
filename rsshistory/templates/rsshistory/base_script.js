let view_display_style = "{{user_config.display_style}}";
let view_display_type = "{{user_config.display_type}}";
let view_show_icons = "{{user_config.show_icons}}" == "True";
let view_small_icons = "{{user_config.small_icons}}" == "True";
let debug = "{{debug}}" == "True"

function getSpinnerText(text = 'Loading...') {
   return `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}`;
}

function putSpinnerOnIt(button) {
    button.prop("disabled", true);

    button.html(
        `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`
    );

    button.parents('form').submit();
}

$(document).ready(function() {
    $("#btnFetch").click(function(event) {
        event.preventDefault();
        putSpinnerOnIt($(this));
    });
});

function getDynamicContent(url_address, htmlElement, attempt = 1, errorInHtml = false) {
    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           $(htmlElement).html(data);
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               getDynamicContent(url_address, htmlElement, attempt + 1, errorInHtml);
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content, retry");
               }
           } else {
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content");
               }
           }
       }
    });
}
function getDynamicJsonContent(url_address, htmlElement, attempt = 1, errorInHtml = false) {
    $.ajax({
       url: url_address,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
         $(htmlElement).html(data.message);
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               getDynamicJsonContent(url_address, htmlElement, attempt + 1, errorInHtml);
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content, retry");
               }
           } else {
               if (errorInHtml) {
                   $(htmlElement).html("Error loading dynamic content");
               }
           }
       }
    });
}

function loadFooterContent() {
    getDynamicJsonContent('{% url 'rsshistory:get-footer-status-line' %}', "#footerLine");
}

function loadMenuContent() {
    getDynamicContent('{% url 'rsshistory:get-menu' %}', "#blockMenu");
}

function getSpinnerText() {
    return `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`
}

$(document).ready(function() {
    loadMenuContent();
    loadFooterContent();

    setInterval(function() {
        loadMenuContent();
        loadFooterContent();
    }, 300000);
});

document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        loadMenuContent();
        loadFooterContent();
    }
});

$('#btnUpdateFooter').on('click', function() {
    loadFooterContent();
});
