
function getEntrySocialData(entry_id, callback = null) {
    let url_address = "{% url 'rsshistory:entry-dislikes' 117 %}".replace("117", entry_id);

    getDynamicJson(url_address, function (data) {
       if (callback) {
         callback(data);
       }
    },
    retry = false);
}


function getEntryOperationalParamters(entry_id, callback=null, attempt = 1) {
    let url_address = "{% url 'rsshistory:entry-op-parameters' 117 %}".replace("117", entry_id);

    getDynamicJson(url_address, function (data) {
       if (callback) {
         callback(data);
       }
    });
}


function isEntry(entry_link, callback=null) {
    let url_address = `{% url 'rsshistory:entry-is' %}?link=${entry_link}`;
    
    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function isSource(source_link, callback=null) {
    let url_address = `{% url 'rsshistory:source-is' %}?link=${source_link}`;
    
    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function getLinkInputSuggestionsJson(page_url, callback=null) {
    let url_address = `{% url 'rsshistory:link-input-suggestions-json' %}?link=${encodeURIComponent(page_url)}`;

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function getSourceInputSuggestionsJson(page_url, callback=null) {
    let url_address = `{% url 'rsshistory:source-input-suggestions-json' %}?link=${encodeURIComponent(page_url)}`;

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function addEntryJson(page_url, browser, callback=null) {
    let url_address = `{% url 'rsshistory:entry-add-json' %}?link=${page_url}&browser=${browser}`;

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function getIndicators(callback=null) {
    let url_address = "{% url 'rsshistory:json-indicators' %}";

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}


function getMenuSearchContainer() {
    let url_address = "{% url 'rsshistory:json-search-container' %}";
    getDynamicJson(url_address, function(data) {
        processMenuData(data, '#MenuSearchContainer');
    });
}


function getMenuGlobalContainer() {
    let url_address = "{% url 'rsshistory:json-global-container' %}";
    getDynamicJson(url_address, function(data) {
        processMenuData(data, '#MenuGlobalContainer');
    });
}


function getMenuPersonalContainer() {
    let url_address = "{% url 'rsshistory:json-personal-container' %}";
    getDynamicJson(url_address, function(data) {
        processMenuData(data, '#MenuPersonalContainer');
    });
}

function getMenuTools() {
    let url_address = "{% url 'rsshistory:json-tools-container' %}";
    getDynamicJson(url_address, function(data) {
        processMenuData(data, '#MenuToolsContainer');
    });
}


function getMenuUsers() {
    let url_address = "{% url 'rsshistory:json-users-container' %}";
    getDynamicJson(url_address, function(data) {
        processMenuData(data, '#MenuUsersContainer');
    });
}

function jsonSourcesInitialize(callback=null) {
    let url_address = "{% url 'rsshistory:json-sources-initialize' %}";
    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function wizardSetupNews(callback=null) {
    let url_address = "{% url 'rsshistory:json-wizard-setup-news' %}";
    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function wizardSetupGallery(callback=null) {
    let url_address = "{% url 'rsshistory:json-wizard-setup-gallery' %}";
    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function wizardSetupSearchEngine(callback=null) {
    let url_address = "{% url 'rsshistory:json-wizard-setup-search-engine' %}";
    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function jsonReadLaterClear(callback=null) {
    let url_address = "{% url 'rsshistory:json-read-later-clear' %}";

    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function jsonReadLaterRemove(entry_id, callback=null) {
    let url_address = "{% url 'rsshistory:json-read-later-remove' 1017 %}".replace("1017", entry_id);

    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}

function getSourceAddForm(page_url, browser, callback=null) {
    let url_address = `{% url 'rsshistory:source-add-form' %}?link=${page_url}&browser=${browser}`;

    getDynamicJson(url_address, function(data) {
       if (callback) {
         callback(data);
       }
    });
}
