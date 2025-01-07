{% load static %}

function getSourceTemplate(source, show_icons = true, small_icons = false) {
    var url = source.url;
    var title = source.title;
    var favicon = source.favicon;
    var url_absolute = source.url_absolute;

    let thumbnail_text = ""; // Declare thumbnail_text once
    if (show_icons) {
        thumbnail_text = `
            <img src="${favicon}" class="content-icon"/>`;
    }

    let additional_text = "";
    if (!source.enabled) {
        additional_text += "[DISABLED]";
    }
    if (source.errors) {
        additional_text += "[ERRORS]";
    }

    var template = `
        <a href="${url_absolute}"
           class="my-1 p-1 list-group-item list-group-item-action rounded border"
           title="${title}">
            ${thumbnail_text}
            <span class="link-list-item-title">
                ${additional_text}
                ${title}
            </span>
            <div class="link-list-item-description">
                ${url}
            </div>
        </a>
    `;

    return template;
}

function fillSourceList(sources) {
    let htmlOutput = '';

    if (sources && sources.length > 0) {
        sources.forEach(source => {
            var template_text = getSourceTemplate(source, view_show_icons, view_small_icons);
            htmlOutput += template_text;
        });
    }

    return htmlOutput;
}

function fillListData() {
    let data = object_list_data;
    $('#listData').html("");

    let sources = data.sources;

    if (!sources || sources.length == 0) {
        $('#listData').html("No sources found");
        return;
    }

    var finished_text = fillSourceList(sources);
    $('#listData').html(finished_text);
    let pagination = GetPaginationNav(data);
    $('#pagination').html(pagination);
}

{% include "rsshistory/javascript_list_utilities.js" %}
