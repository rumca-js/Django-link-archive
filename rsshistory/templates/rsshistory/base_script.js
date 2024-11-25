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

function add_text(error_line, text) {
    if (error_line == "") {
        error_line = text;
    }
    else {
        error_line += ", " + text;
    }

    return error_line;
}

function SetMenuStatusLine() {
       if (common_indicators.read_later_queue.status) {
           showElement(".readLaterElement");
       }
       else {
           hideElement(".readLaterElement");
       }
       if (common_indicators.sources_error.status) {
           showElement(".sourceErrorElement");
       }
       else {
           hideElement(".sourceErrorElement");
       }
       if (common_indicators.threads_error.status) {
           showElement(".configurationErrorElement");
       }
       else {
           hideElement(".configurationErrorElement");
       }
       if (common_indicators.configuration_error.status ||
           common_indicators.jobs_error.status) {
           showElement(".adminErrorElement");
       }
       else {
           hideElement(".adminErrorElement");
       }
}

function SetFooterStatusLine() {
   let error_line = "";

   if (common_indicators.sources_error.status) {
       error_line = add_text(error_line, "Sources");
   }
   if (common_indicators.threads_error.status) {
       error_line = add_text(error_line, "Threads");
   }
   if (common_indicators.jobs_error.status) {
       error_line = add_text(error_line, "Jobs");
   }
   if (common_indicators.configuration_error.status) {
       error_line = add_text(error_line, "Configuration");
   }

   $("#footerLine").html(error_line);
}

let common_indicators = null;

function showElement(element) {
   $(element).show();
   $(element).removeClass("invisible");
}
function hideElement(element) {
   $(element).hide();
   $(element).addClass("invisible");
}

let currentgetIndicators = 0;
function getIndicators(attempt=1) {
    let requestCurrentgetIndicators = ++currentgetIndicators;

    let url = '{% url 'rsshistory:get-indicators' %}';
    
    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
           if (requestCurrentgetIndicators != currentgetIndicators)
           {
               return;
           }
           common_indicators = data.indicators;

           SetMenuStatusLine();
           SetFooterStatusLine();
       },
       error: function(xhr, status, error) {
           if (requestCurrentgetIndicators != currentgetIndicators)
           {
               return;
           }
           
           if (attempt < 3) {
               getIndicators(attempt + 1);
           } else {
           }
       }
    });
}

$(document).ready(function() {
    getIndicators();

    setInterval(function() {
        getIndicators();
    }, 300000);
});

document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        getIndicators();
    }
});
