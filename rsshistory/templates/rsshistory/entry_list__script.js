{% load static %}


let show_pure_links = 0;
let highlight_bookmarks = false;


function getVotesBadge(page_rating_votes) {
    let badge_text = page_rating_votes > 0 ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 30px; font-size: 0.8rem;">
            ${page_rating_votes}
        </span>` : '';

    return badge_text;
}


function getBookmarkBadge(entry) {
    let badge_star = entry.bookmarked ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 5px; right: 5px; font-size: 0.8rem;">
            ★
        </span>` : '';
    return badge_star;
}


function getAgeBadge(entry) {
    let badge_text = entry.age > 0 ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 30px; right: 5px; font-size: 0.8rem;">
            A
        </span>` : '';
    return badge_text;
}


function getDeadBadge(entry) {
    let badge_text = entry.date_dead_since ? `
        <span class="badge text-bg-warning" style="position: absolute; top: 30px; right: 30px; font-size: 0.8rem;">
            D
        </span>` : '';
    return badge_text;
}


function getEntryTags(entry) {
    let tags_text = "";
    if (entry.tags && entry.tags.length > 0) {
        tags_text = entry.tags.map(tag => `#${tag}`).join(",");
        tags_text = `<div class="text-reset mx-2">` + tags_text + `</div>`;
    }
    return tags_text;
}


function isEntryValid(entry) {
    if (!entry.is_valid || entry.date_dead_since) {
        return false;
    }
    return true;
}


function entryStandardTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = getVotesBadge(page_rating_votes);
    let badge_star = getBookmarkBadge(entry);
    let badge_age = getAgeBadge(entry);

    let bookmark_class = entry.bookmarked ? `list-group-item-primary` : '';
    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;

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

    let tags_text = getEntryTags(entry);

    return `
        <a 
            href="{entry_link}"
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
                    ${tags_text}
                </div>
            </div>

            ${badge_text}
            ${badge_star}
            ${badge_age}
        </a>
    `;
}


function entrySearchEngineTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = getVotesBadge(page_rating_votes);
    let badge_star = highlight_bookmarks ? getBookmarkBadge(entry) : "";
    let badge_age = getAgeBadge(entry);
   
    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;
    let bookmark_class = (entry.bookmarked && highlight_bookmarks) ? `list-group-item-primary` : '';

    let thumbnail_text = '';
    if (show_icons) {
        const iconClass = small_icons ? 'icon-small' : 'icon-normal';
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                <img src="{thumbnail}" class="rounded ${iconClass}"/>
            </div>`;
    }

    let tags_text = getEntryTags(entry);

    return `
        <a 
            href="{entry_link}"
            title="{title}"
            ${invalid_style}
            class="my-1 p-1 list-group-item list-group-item-action ${bookmark_class}"
        >
            <div class="d-flex">
               ${thumbnail_text}
               <div class="mx-2">
                  <span style="font-weight:bold" class="text-reset">{title_safe}</span>
                  <div class="text-reset text-decoration-underline">@ {link}</div>
                  ${tags_text}
                  ${badge_text}
                  ${badge_star}
                  ${badge_age}
               </div>
            </div>
        </a>
    `;
}


function entryGalleryTemplate(entry, show_icons = true, small_icons = false) {
    if (isMobile()) {
        return entryGalleryTemplateMobile(entry, show_icons, small_icons);
    }
    else {
        return entryGalleryTemplateDesktop(entry, show_icons, small_icons);
    }
}


function entryGalleryTemplateDesktop(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;
    
    let badge_text = getVotesBadge(page_rating_votes);
    let badge_star = getBookmarkBadge(entry);
    let badge_age = getAgeBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;

    let thumbnail = entry.thumbnail;
    let thumbnail_text = `
        <img src="${thumbnail}" style="width:100%;max-height:100%;aspect-ratio:3/4;object-fit:cover;"/>
        ${badge_text}
        ${badge_star}
        ${badge_age}
    `;

    let tags_text = getEntryTags(entry);

    return `
        <a 
            href="{entry_link}"
            title="{title}"
            ${invalid_style}
            class="element_${view_display_type} list-group-item list-group-item-action m-1"
        >
            <div style="display: flex; flex-direction:column; align-content:normal; height:100%">
                <div style="flex: 0 0 70%; flex-shrink: 0;flex-grow:0;max-height:70%">
                    ${thumbnail_text}
                </div>
                <div style="flex: 0 0 30%; flex-shrink: 0;flex-grow:0;max-height:30%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    <span style="font-weight: bold" class="text-primary">{title_safe}</span>
                    <div class="link-list-item-description">{source__title}</div>
                    ${tags_text}
                </div>
            </div>
        </a>
    `;
}


function entryGalleryTemplateMobile(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;
    
    let badge_text = getVotesBadge(page_rating_votes);
    let badge_star = getBookmarkBadge(entry);
    let badge_age = getAgeBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;

    let thumbnail = entry.thumbnail;
    let thumbnail_text = `
        <img src="${thumbnail}" style="width:100%; max-height:100%; object-fit:cover"/>
        ${badge_text}
        ${badge_star}
        ${badge_age}
    `;

    let tags_text = getEntryTags(entry);

    return `
        <a 
            href="{entry_link}"
            title="{title}"
            ${invalid_style}
            class="list-group-item list-group-item-action"
        >
            <div style="display: flex; flex-direction:column; align-content:normal; height:100%">
                <div style="flex: 0 0 70%; flex-shrink: 0;flex-grow:0;max-height:70%">
                    ${thumbnail_text}
                </div>
                <div style="flex: 0 0 30%; flex-shrink: 0;flex-grow:0;max-height:30%">
                    <span style="font-weight: bold" class="text-primary">{title_safe}</span>
                    <div class="link-list-item-description">{source__title}</div>
                    ${tags_text}
                </div>
            </div>
        </a>
    `;
}


function fillOneEntry(entry) {
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

    let entry_link = show_pure_links ? entry.link : entry.link_absolute;

    title = escapeHtml(entry.title)

    let title_safe = null;
    if (entry.title_safe) {
       title_safe = escapeHtml(entry.title_safe)
    }
    else
    {
       title_safe = escapeHtml(entry.title)
    }
    let source__title = null;
    if (entry.source__title) {
       source__title = escapeHtml(entry.source__title)
    }

    // Replace all occurrences of the placeholders using a global regular expression
    let listItem = template_text
        .replace(/{link_absolute}/g, entry.link_absolute)
        .replace(/{link}/g, entry.link)
        .replace(/{entry_link}/g, entry_link)
        .replace(/{title}/g, title)
        .replace(/{thumbnail}/g, entry.thumbnail)
        .replace(/{title_safe}/g, title_safe)
        .replace(/{page_rating_votes}/g, entry.page_rating_votes)
        .replace(/{page_rating_contents}/g, entry.page_rating_contents)
        .replace(/{page_rating}/g, entry.page_rating)
        .replace(/{source__title}/g, source__title)
        .replace(/{age}/g, entry.age)
        .replace(/{date_published}/g, datePublished.toLocaleString());

    return listItem;
}


function fillEntryList(entries) {
    let htmlOutput = '';

    if (view_display_type == "gallery")
    {
        htmlOutput = `  <span class="d-flex flex-wrap">`;
    }
    else
    {
        htmlOutput = `  <span class="container list-group">`;
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

    htmlOutput += `</span>`;

    return htmlOutput;
}


function fillListData() {
    let data = object_list_data;

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


$(document).on("click", '#showPureLinks', function(e) {
   if (show_pure_links) {
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
