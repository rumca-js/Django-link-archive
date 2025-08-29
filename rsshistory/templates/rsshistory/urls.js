
function getEntryDislikeData(entry_id, callback = null, attempt = 1) {
    let url_address = "{% url 'rsshistory:entry-dislikes' 117 %}".replace("117", entry_id);

    getDynamicJson(url_address, function (data) {
       if (callback) {
         callback(data);
       }
    });
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


function addEntryJson(page_url, callback=null) {
    let url_address = `{% url 'rsshistory:entry-add-json' %}?link=${page_url}&browser=${browser}`;

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    });
}
