let view_display_style = "{{user_config.display_style}}";
let view_display_type = "{{user_config.display_type}}";
let view_show_icons = "{{user_config.show_icons}}" == "True";
let view_small_icons = "{{user_config.small_icons}}" == "True";
let debug = "{{debug}}" == "True"


$(document).ready(function() {
   $("#btnFetch").click(function(event) {
       event.preventDefault();
       putSpinnerOnIt($(this));
   });
});

function loadFooterContent() {
    getDynamicJsonContent('{% url 'rsshistory:get-footer-status-line' %}', "#footerLine");
}

function loadMenuContent() {
//    getDynamicContent('{% url 'rsshistory:get-menu' %}', "#blockMenu");
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
