let view_display_style = "{{user_config.display_style}}";
let view_display_type = "{{user_config.display_type}}";
let view_show_icons = "{{user_config.show_icons}}" == "True";
let view_small_icons = "{{user_config.small_icons}}" == "True";
let debug = "{{debug}}" == "True"


let common_indicators = null;


$(document).ready(function() {
   $("#btnFetch").click(function(event) {
       event.preventDefault();
       putSpinnerOnIt($(this));
   });
});


function add_text(error_line, text) {
    let result = "";
    if (error_line == "") {
        result = text;
    }
    else {
        result += ", " + text;
    }

    return result;
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
       error_line += add_text(error_line, "Sources");
   }
   if (common_indicators.threads_error.status) {
       error_line += add_text(error_line, "Threads");
   }
   if (common_indicators.jobs_error.status) {
       error_line += add_text(error_line, "Jobs");
   }
   if (common_indicators.configuration_error.status) {
       error_line += add_text(error_line, "Configuration");
   }
   if (common_indicators.internet_error.status) {
       error_line += add_text(error_line, "Internet");
   }
   if (common_indicators.crawling_server_error.status) {
       error_line += add_text(error_line, "Crawling server");
   }
   if (common_indicators.is_reading.status) {
       error_line += add_text(error_line, common_indicators.is_reading.message);
   }

   if (error_line == "") {
       $("#footerLine").html("");
       $("#footerLine").hide();
   }
   else {
       $("#footerLine").html(error_line);
       $("#footerLine").show();
   }
}


function showElement(element) {
   $(element).show();
   $(element).removeClass("invisible");
}


function hideElement(element) {
   $(element).hide();
   $(element).addClass("invisible");
}


function setLightMode() {
    view_display_style = "style-light";

    const linkElement = document.querySelector('link[rel="stylesheet"][href*="styles.css_style-"]');
    if (linkElement) {
        // TODO replace rsshistory with something else
        //linkElement.href = "/django/rsshistory/css/styles.css_style-light.css";
    }

    const htmlElement = document.documentElement;
    htmlElement.setAttribute("data-bs-theme", "light");

    const navbar = document.getElementById('navbar');
    navbar.classList.remove('navbar-light', 'bg-dark');
    navbar.classList.add('navbar-dark', 'bg-light');
}


function setDarkMode() {
    view_display_style = "style-dark";

    const linkElement = document.querySelector('link[rel="stylesheet"][href*="styles.css_style-"]');
    if (linkElement) {
        //linkElement.href = "/django/rsshistory/css/styles.css_style-dark.css";
    }

    const htmlElement = document.documentElement;
    htmlElement.setAttribute("data-bs-theme", "dark");

    const navbar = document.getElementById('navbar');
    navbar.classList.remove('navbar-light', 'bg-light');
    navbar.classList.add('navbar-dark', 'bg-dark');
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
