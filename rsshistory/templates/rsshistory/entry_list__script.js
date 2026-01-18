{% load static %}


function fillEntryList(entries) {
    let htmlOutput = '';

    htmlOutput = `  <span class="container list-group">`;

    if (view_display_type == "gallery")
    {
        htmlOutput += `  <span class="d-flex flex-wrap">`;
    }

    if (entries && entries.length > 0) {
        entries.forEach(entry => {
            const listItem = getOneEntryEntryText(entry);

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


{% include "rsshistory/javascript_list_utilities.js" %}
{% include "rsshistory/urls.js" %}


$(document).on("click", '#showPureLinks', function(e) {
   if (!entries_direct_links) {
      entries_direct_links = true;
   }
   else {
      entries_direct_links = false;
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


$(document).on("click", 'input[name="viewMode"]', function(e) {
    view_display_type = $(this).val();
    fillListData();
});


$(document).on('change', 'input[name="theme"]', function () {
    view_display_style = $(this).val();

    if (view_display_style == "style-light") {
        setLightMode();
    }
    else {
        setDarkMode();
    }

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
