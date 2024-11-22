{% load static %}

function entryStandardTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = page_rating_votes > 0 ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 30px; font-size: 1rem;">
            ${page_rating_votes}
        </span>` : '';

    let badge_star = entry.bookmarked ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 5px; font-size: 1rem;">
            ★
        </span>` : '';

    let bookmark_class = entry.bookmarked ? `list-group-item-primary` : '';
    let invalid_style = entry.is_valid ? `` : `style="opacity: 0.5"`;
    let votes_text = page_rating_votes > 0 ? `[${page_rating_votes}]` : '';

    let img_text = '';
    if (show_icons) {
        const iconClass = small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="{thumbnail}" class="rounded ${iconClass}" />`;
    }
    
    let thumbnail_text = '';
    if (img_text) {
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                ${img_text}
            </div>`;
    }

    return `
        <a 
            href="{link_absolute}"
            title="{title}"
            ${invalid_style}
            class="my-1 p-1 list-group-item list-group-item-action ${bookmark_class}"
        >
            <div class="d-flex">
                ${thumbnail_text}
                <div class="mx-2">
                    <span style="font-weight:bold" class="text-reset">{title_safe}</span>
                    <div class="text-reset">
                        {source__title} {date_published}
                    </div>
                </div>
            </div>

            ${badge_text}
            ${badge_star}
        </a>
    `;
}

function entrySearchEngineTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = page_rating_votes > 0 ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 30px; font-size: 1rem;">
            ${page_rating_votes}
        </span>` : '';

    let badge_star = entry.bookmarked ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 5px; font-size: 1rem;">
            ★
        </span>` : '';

    let invalid_style = entry.is_valid ? `` : `style="opacity: 0.5"`;
    let bookmark_class = entry.bookmarked ? `list-group-item-primary` : '';

    let votes_text = page_rating_votes > 0 ? `[${page_rating_votes}]` : '';

    let thumbnail_text = '';
    if (show_icons) {
        const iconClass = small_icons ? 'icon-small' : 'icon-normal';
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                <img src="{thumbnail}" class="rounded ${iconClass}"/>
            </div>`;
    }

    return `
        <a 
            href="{link_absolute}"
            title="{title}"
            ${invalid_style}
            class="my-1 p-1 list-group-item list-group-item-action ${bookmark_class}"
        >
            <div class="d-flex">
               ${thumbnail_text}
               <div class="mx-2">
                  <span style="font-weight:bold" class="text-reset">{title_safe}</span>
                  <div class="text-reset">@ {link}</div>
                  ${badge_text}
                  ${badge_star}
               </div>
            </div>
        </a>
    `;
}

function entryGalleryTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;
    
    let badge_text = page_rating_votes > 0 ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 30px; font-size: 1rem;">
            ${page_rating_votes}
        </span>` : '';

    let star_badge = entry.bookmarked ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 5px; font-size: 1rem;">
            ★
        </span>` : '';
    let invalid_style = entry.is_valid ? `` : `style="opacity: 0.5"`;

    let thumbnail = entry.thumbnail;
    let thumbnail_text = `
        <img src="${thumbnail}" style="width:100%; max-height:100%; object-fit:cover"/>
        ${badge_text}
        ${star_badge}
    `;

    return `
        <a 
            href="{link_absolute}"
            title="{title}"
    ${invalid_style}
            class="element_${view_display_type} list-group-item list-group-item-action"
        >
            <div style="display: flex; flex-direction:column; align-content:normal; height:100%">
                <div style="flex: 0 0 70%; flex-shrink: 0;flex-grow:0;max-height:70%">
                    ${thumbnail_text}
                </div>
                <div style="flex: 0 0 30%; flex-shrink: 0;flex-grow:0;max-height:30%">
                    <span style="font-weight: bold" class="text-primary">{title_safe}</span>
                    <div class="link-list-item-description">{source__title}</div>
                </div>
            </div>
        </a>
    `;
}

function fillEntryList(entries) {
    let htmlOutput = '';

    if (entries && entries.length > 0) {
        entries.forEach(entry => {
            let datePublished = new Date(entry.date_published);
            if (isNaN(datePublished)) {
                datePublished = new Date();
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

            let thumbnail = entry.thumbnail;
            let page_rating_votes = entry.page_rating_votes;
            let page_rating_contents = entry.page_rating_contents;

            // Replace all occurrences of the placeholders using a global regular expression
            let listItem = template_text
                .replace(/{link_absolute}/g, entry.link_absolute)
                .replace(/{link}/g, entry.link)
                .replace(/{title}/g, entry.title)
                .replace(/{thumbnail}/g, entry.thumbnail)
                .replace(/{title_safe}/g, entry.title_safe)
                .replace(/{page_rating_votes}/g, entry.page_rating_votes)
                .replace(/{page_rating_contents}/g, entry.page_rating_contents)
                .replace(/{page_rating}/g, entry.page_rating)
                .replace(/{source__title}/g, entry.source__title)
                .replace(/{date_published}/g, datePublished.toLocaleString());

            htmlOutput += listItem;
        });
    } else {
        htmlOutput = '<li class="list-group-item">No entries found</li>';
    }

    return htmlOutput;
}

function fillListData(data) {
    $('#listData').html("");

    let entries = data.entries;

    if (!entries || entries.length == 0) {
        $('#listData').html("No entries found");
        $('#pagination').html("");
        return;
    }

    var finished_text = fillEntryList(entries);
    $('#listData').html(finished_text);
    let pagination = GetPaginationNav(data);
    $('#pagination').html(pagination);
}

{% include "rsshistory/javascript_list_utilities.js" %}
