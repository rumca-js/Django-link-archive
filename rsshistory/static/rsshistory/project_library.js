// Things that come from config
let entries_visit_alpha=1.0;
let entries_dead_alpha=0.5;

// user configuration things
let view_display_style = "style-light";
let view_display_type = "standard";
let view_show_icons = false;
let view_small_icons = false;
let user_age = 18;
let debug_mode = false;

// other global variables
let search_suggestions = [];
let common_indicators = null;

let highlight_bookmarks = false;
let show_pure_links = false;
let default_page_size = 200;
let sort_function = "-date_published";


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


function setDisplayMode() {
    if (view_display_style == "style-light") {
       setLightMode();

    }
    if (view_display_style == "style-dark") {
       setDarkMode();
    }
}


function SetMenuStatusLine() {
       if (common_indicators.check_later_queue.status) {
           showElement("#PersonalMenuPill");
           showElement(".readLaterElement");
       }
       else {
           hideElement("#PersonalMenuPill");
           hideElement(".readLaterElement");
       }
       if (common_indicators.sources_error.status) {
           showElement("#GlobalMenuPill");
           showElement(".sourceErrorElement");
       }
       else {
           hideElement("#GlobalMenuPill");
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

       if (common_indicators.configuration_error.status ||
           common_indicators.jobs_error.status ||
           common_indicators.threads_error.status) {
           showElement("#UserMenuPill");
       }
       else {
           hideElement("#UserMenuPill");
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
    navbar.classList.remove('navbar-dark', 'bg-dark');
    navbar.classList.add('navbar-light', 'bg-light');

    let icons = document.querySelectorAll('.mainbutton-icon');

    icons.forEach(icon => {
        icon.style.filter = "";
    });

    icons = document.querySelectorAll('.content-icon');

    icons.forEach(icon => {
        icon.style.filter = "";
    });
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

    let icons = document.querySelectorAll('.mainbutton-icon');

    icons.forEach(icon => {
        icon.style.filter = 'invert(1)';
    });

    icons = document.querySelectorAll('.content-icon');

    icons.forEach(icon => {
        icon.style.filter = 'invert(1)';
    });
}


function processMenuData(data, container) {
    let finished_text = `
    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
       ${data.title}
       <span class="position-absolute top-5 start-95 translate-middle badge rounded-pill bg-danger invisible" id="${data.title}MenuPill">
           !
           <span class="visually-hidden">Error</span>
       </span>
    </a>
    <ul class="dropdown-menu">
        `;


    let style_text = "";
    if (view_display_style == "style-dark") {
        style_text = "filter:invert(1)";
    }

    data.rows.forEach(row => {

       finished_text += `
       <li>
         <a href="${row.link}" class="dropdown-item" title="${row.title}">
           <img src="${row.icon}" class="mainbutton-icon" style="${style_text}"/>
           ${row.title}
         </a>
       </li>
       `;
    });

    finished_text += "</ul>"

    $(container).html(finished_text);
}
