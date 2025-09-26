{% load static %}


function fillOneEntry(entry) {
    let datePublishedStr = "";
    if (entry.date_published) {
        let datePublished = new Date(entry.date_published);
        if (!isNaN(datePublished)) {
            datePublishedStr = datePublished.toLocaleString();
        }
    }

    const templateMap = {
        "standard": entryStandardTemplate,
        "gallery": entryGalleryTemplate,
        "search-engine": entrySearchEngineTemplate
    };

    const templateFunc = templateMap[view_display_type];
    if (!templateFunc) {
        return;
    }
    var template_text = templateFunc(entry, view_show_icons, view_small_icons);

    return template_text;
}


function fillEntryList(entries) {
    let htmlOutput = '';

    htmlOutput = `  <span class="container list-group">`;

    if (view_display_type == "gallery")
    {
        htmlOutput += `  <span class="d-flex flex-wrap">`;
    }

    if (entries && entries.length > 0) {
        entries.forEach(entry => {
            const listItem = fillOneEntry(entry);

            if (listItem) {
                htmlOutput += listItem;
            }
        });
    } else {
        htmlOutput = '<li class="list-group-item">No entries found</li>';
    }

    if (view_display_type == "gallery")
    {
        htmlOutput += `</span>`;
    }

    htmlOutput += `</span>`;

    return htmlOutput;
}


function GetQueryDetailsHtml(data) {
    htmlOutput = "";

    let execution_time = data.timestamp_s;
    let conditions = data.conditions;
    let errors = data.errors;

    htmlOutput += `<div>Execution Time:${execution_time}</div>`;
    htmlOutput += `<div>Conditions:${conditions}</div>`;

    if (errors && errors.length > 0) {
        htmlOutput += `<div>Errors</div>`;

        errors.forEach(error => {
            htmlOutput += `<div>${error}</div>`;
        });
    }

    return htmlOutput;
}


function fillListData() {
    let data = object_list_data;

    if (!data) {
        $('#listData').html("");
        $('#pagination').html("");
        return;
    }

    $('#listData').html("");

    let entries = data.entries;

    if (!entries || entries.length == 0) {
        $('#listData').html("No entries found");
        $('#pagination').html("");
    }
    else {
        var finished_text = fillEntryList(entries);
        $('#listData').html(finished_text);
        let pagination = GetPaginationNav(data.page, data.num_pages, data.count);
        $('#pagination').html(pagination);

        fillEntryDislikes(entries);
    }

    fillErrors(data.errors);

    if (debug_mode) {
       let query_info = GetQueryDetailsHtml(data);
       $('#queryInfo').html(query_info);
    }
}


function fillErrors(errors) {
   if (errors == null) {
      return null;
   }

   text = "";
   errors.forEach(error => {
	   text += `<div>${error}</div>`;
   });
   $('#queryInfo').html(text);
}


function fillEntryDislikes(entries) {
    entry_list_social = new Map();

    if (entries && entries.length > 0) {
        for(let i = 0; i < entries.length; i++) {
           const entry = entries[i];

           // TODO setTimeout will not be necessary if
           // https://github.com/rumca-js/crawler-buddy/issues/176 is solved

           setTimeout(() => {
             getEntrySocialData(entry.id, function (data) {
                let entry_parameters = getEntrySocialDataText(data);
                entry_list_social.set(entry.id, entry_parameters);
  
                let upvote_ratio_div = `<div>${entry_parameters}</div>`;

                $(`[entry="${entry.id}"] [entryDetails="true"]`).append(upvote_ratio_div);
             })
	   }, i * 100);
        };
    }
}


{% include "rsshistory/javascript_list_utilities.js" %}
{% include "rsshistory/urls.js" %}


$(document).on("click", '#showPureLinks', function(e) {
   if (!show_pure_links) {
      show_pure_links = true;
   }
   else {
      show_pure_links = false;
   }

   fillListData();
});


$(document).on("click", '#highlightBookmarks', function(e) {
   if (!highlight_bookmarks) {
      highlight_bookmarks = true;
   }
   else {
      highlight_bookmarks = false;
   }

   fillListData();
});


$(document).on("click", '#displayStandard', function(e) {
    view_display_type = "standard";
    fillListData();
});


$(document).on("click", '#displayGallery', function(e) {
    view_display_type = "gallery";
    fillListData();
});


$(document).on("click", '#displaySearchEngine', function(e) {
    view_display_type = "search-engine";
    fillListData();
});


$(document).on("click", '#displayLight', function(e) {
    setLightMode();

    fillListData();
});


$(document).on("click", '#displayDark', function(e) {
    setDarkMode();

    fillListData();
});


$(document).on("click", '.user-history-remove', function(e) {
    e.preventDefault();

    search_id = $(this).data('search-id');

    url = `{% url "rsshistory:user-search-history-remove"  117 %}`.replace("117", search_id);

    getDynamicJson(url, function(data) {
        if (data.status) {
           loadSearchHistory();
	}
    });
});
