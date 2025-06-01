{% load static %}
/*
 * requires
 *  - show_pure_link
 *  - highlight_bookmarks
 */


function isEntryValid(entry) {
    return entry.is_valid;
}



function getEntryVotesBadge(entry, overflow=false) {
    let style = "font-size: 0.8rem;"
    if (overflow) {
        style = "position: absolute; top: 5px; right: 30px;" + style;
    }

    let badge_text = entry.page_rating_votes > 0 ? `
        <span class="badge text-bg-warning" style="${style}">
            ${entry.page_rating_votes}
        </span>` : '';

    return badge_text;
}


function getEntryBookmarkBadge(entry, overflow=false) {
    let style = "font-size: 0.8rem;"
    if (overflow) {
        style = "position: absolute; top: 5px; right: 5px;" + style;
    }

    let badge_star = entry.bookmarked ? `
        <span class="badge text-bg-warning" style="${style}">
            ★
        </span>` : '';
    return badge_star;
}


function getEntryAgeBadge(entry, overflow=false) {
    let style = "font-size: 0.8rem;"
    if (overflow) {
        style = "position: absolute; top: 30px; right: 5px;" + style;
    }

    let badge_text = entry.age > 0 ? `
        <span class="badge text-bg-warning" style="${style}">
            A
        </span>` : '';
    return badge_text;
}


function getEntryDeadBadge(entry, overflow=false) {
    let style = "font-size: 0.8rem;"
    if (overflow) {
        style = "position: absolute; top: 30px; right: 30px;" + style;
    }

    let badge_text = entry.date_dead_since ? `
        <span class="badge text-bg-warning" style="${style}">
           💀
        </span>` : '';
    return badge_text;
}


function getEntryTags(entry) {
    let tags_text = "";
    if (entry.tags && entry.tags.length > 0) {
        tags_text = entry.tags.map(tag => `#${tag}`).join(",");
    }
    return tags_text;
}


function getEntryLinkText(entry) {
    let link = entry.link;
    return `<div class="text-reset text-decoration-underline">@ ${link}</div>`;
}


function getEntrySourceTitle(entry) {
    let source__title = "";
    if (entry.source__title) {
       source__title = escapeHtml(entry.source__title)
    }
    return source__title;
}


function getEntryDatePublished(entry) {
    let datePublishedStr = "";
    if (entry.date_published) {
        let datePublished = new Date(entry.date_published);
        if (!isNaN(datePublished)) {
            datePublishedStr = datePublished.toLocaleString();
        }
    }

    return datePublishedStr;
}


function getEntryTitleSafe(entry) {
    let title_safe = "";
    if (entry.title_safe) {
       title_safe = escapeHtml(entry.title_safe)
    }
    else
    {
       title_safe = escapeHtml(entry.title)
    }

    return title_safe;
}


function entryStandardTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = getEntryVotesBadge(entry);
    let badge_star = getEntryBookmarkBadge(entry);
    let badge_age = getEntryAgeBadge(entry);
    let badge_dead = getEntryDeadBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;
    let bookmark_class = entry.bookmarked ? `list-group-item-primary` : '';
    let thumbnail = entry.thumbnail;

    let img_text = '';
    if (show_icons) {
        const iconClass = small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }
    
    let thumbnail_text = '';
    if (img_text) {
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                ${img_text}
            </div>`;
    }
    let tags_text = getEntryTags(entry);
    let tags = `<div class="text-reset mx-2">${tags_text}</div>`;
    let source__title = getEntrySourceTitle(entry);
    let date_published = getEntryDatePublished(entry);
    let title_safe = getEntryTitleSafe(entry);
    let hover_title = title_safe + " " + tags_text;
    let entry_link = show_pure_links ? entry.link : entry.link_absolute;

    return `
        <a 
            href="${entry_link}"
            title="${hover_title}"
            ${invalid_style}
            class="my-1 p-1 list-group-item list-group-item-action ${bookmark_class} border rounded"
        >
            <div class="d-flex">
                ${thumbnail_text}
                <div class="mx-2">
                    <span style="font-weight:bold" class="text-reset">${title_safe}</span>
                    <div class="text-reset">
                        ${source__title} ${date_published}
                    </div>
                    ${tags}
                </div>

                <div class="mx-2 ms-auto">
                  ${badge_text}
                  ${badge_star}
                  ${badge_age}
                  ${badge_dead}
                </div>
            </div>
        </a>
    `;
}


function entrySearchEngineTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = getEntryVotesBadge(entry);
    let badge_star = getEntryBookmarkBadge(entry);
    let badge_age = getEntryAgeBadge(entry);
    let badge_dead = getEntryDeadBadge(entry);
   
    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;
    let bookmark_class = (entry.bookmarked && highlight_bookmarks) ? `list-group-item-primary` : '';

    let thumbnail = entry.thumbnail;

    let thumbnail_text = '';
    if (show_icons) {
        const iconClass = small_icons ? 'icon-small' : 'icon-normal';
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                <img src="${thumbnail}" class="rounded ${iconClass}"/>
            </div>`;
    }
    let tags_text = getEntryTags(entry);
    let tags = `<div class="text-reset mx-2">${tags_text}</div>`;
    let title_safe = getEntryTitleSafe(entry);
    let entry_link = show_pure_links ? entry.link : entry.link_absolute;
    let hover_title = title_safe + " " + tags_text;
    let link = entry.link;

    let link_text = getEntryLinkText(entry);

    return `
        <a 
            href="${entry_link}"
            title="${hover_title}"
            ${invalid_style}
            class="my-1 p-1 list-group-item list-group-item-action ${bookmark_class} border rounded"
        >
            <div class="d-flex">
               ${thumbnail_text}
               <div class="mx-2">
                  <span style="font-weight:bold" class="text-reset">${title_safe}</span>
		  ${link_text}
                  ${tags}
               </div>

               <div class="mx-2 ms-auto">
                  ${badge_text}
                  ${badge_star}
                  ${badge_age}
                  ${badge_dead}
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
    
    let badge_text = getEntryVotesBadge(entry, true);
    let badge_star = getEntryBookmarkBadge(entry, true);
    let badge_age = getEntryAgeBadge(entry, true);
    let badge_dead = getEntryDeadBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `opacity: 0.5`;
    let bookmark_class = (entry.bookmarked && highlight_bookmarks) ? `list-group-item-primary` : '';

    let thumbnail = entry.thumbnail;
    let thumbnail_text = `
        <img src="${thumbnail}" style="width:100%;max-height:100%;aspect-ratio:3/4;object-fit:cover;"/>
        <div class="ms-auto">
            ${badge_text}
            ${badge_star}
            ${badge_age}
            ${badge_dead}
        </div>
    `;

    let tags_text = getEntryTags(entry);
    let tags = `<div class="text-reset mx-2">${tags_text}</div>`;

    let title_safe = getEntryTitleSafe(entry);
    let hover_title = title_safe + " " + tags_text;
    let entry_link = show_pure_links ? entry.link : entry.link_absolute;
    let source__title = getEntrySourceTitle(entry);

    return `
        <a 
            href="${entry_link}"
            title="${hover_title}"
            class="list-group-item list-group-item-action m-1 border rounded p-2"
            style="text-overflow: ellipsis; max-width: 18%; min-width: 18%; width: auto; aspect-ratio: 1 / 1; text-decoration: none; display:flex; flex-direction:column; ${invalid_style}"
        >
            <div style="display: flex; flex-direction:column; align-content:normal; height:100%">
                <div style="flex: 0 0 70%; flex-shrink: 0;flex-grow:0;max-height:70%">
                    ${thumbnail_text}
                </div>
                <div style="flex: 0 0 30%; flex-shrink: 0;flex-grow:0;max-height:30%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    <span style="font-weight: bold" class="text-primary">${title_safe}</span>
                    <div class="link-list-item-description">${source__title}</div>
                    ${tags}
                </div>
            </div>
        </a>
    `;
}


function entryGalleryTemplateMobile(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;
    
    let badge_text = getEntryVotesBadge(entry, true);
    let badge_star = getEntryBookmarkBadge(entry, true);
    let badge_age = getEntryAgeBadge(entry, true);
    let badge_dead = getEntryDeadBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `opacity: 0.5`;
    let bookmark_class = (entry.bookmarked && highlight_bookmarks) ? `list-group-item-primary` : '';

    let thumbnail = entry.thumbnail;
    let thumbnail_text = `
        <img src="${thumbnail}" style="width:100%; max-height:100%; object-fit:cover"/>
        ${badge_text}
        ${badge_star}
        ${badge_age}
        ${badge_dead}
    `;

    let tags_text = getEntryTags(entry);
    let tags = `<div class="text-reset mx-2">${tags_text}</div>`;

    let source__title = getEntrySourceTitle(entry);
    let title_safe = getEntryTitleSafe(entry);
    let hover_title = title_safe + " " + tags_text;

    let entry_link = show_pure_links ? entry.link : entry.link_absolute;

    return `
        <a 
            href="${entry_link}"
            title="${hover_title}"
            class="list-group-item list-group-item-action border rounded p-2"
            style="text-overflow: ellipsis; max-width: 100%; min-width: 100%; width: auto; aspect-ratio: 1 / 1; text-decoration: none; display:flex; flex-direction:column; ${invalid_style} ${bookmark_class}"
        >
            <div style="display: flex; flex-direction:column; align-content:normal; height:100%">
                <div style="flex: 0 0 70%; flex-shrink: 0;flex-grow:0;max-height:70%">
                    ${thumbnail_text}
                </div>
                <div style="flex: 0 0 30%; flex-shrink: 0;flex-grow:0;max-height:30%">
                    <span style="font-weight: bold" class="text-primary">${title_safe}</span>
                    <div class="link-list-item-description">${source__title}</div>
                    ${tags}
                </div>
            </div>
        </a>
    `;
}


function getEntryVisitsBar(entry) {
    let link_absolute = entry.link_absolute;
    let id = entry.id;
    let title = entry.title;
    let title_safe = getEntryTitleSafe(entry);
    let link = entry.link;
    let thumbnail = entry.thumbnail;
    let source__title = entry.source__title;
    let date_published = getEntryDatePublished(entry);
    let date_last_visit = entry.date_last_visit.toLocaleString();
    let number_of_visits = entry.number_of_visits;

    let badge_text = getEntryVotesBadge(entry, true);
    let badge_star = getEntryBookmarkBadge(entry, true);
    let badge_age = getEntryAgeBadge(entry, true);
    let badge_dead = getEntryDeadBadge(entry, true);

    let img_text = '';
    if (view_show_icons) {
        const iconClass = view_small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }
    let link_text = getEntryLinkText(entry);

    let text = `
         <a
         class="list-group-item list-group-item-action"
         href="${link_absolute}" title="${title}">
             ${badge_text}
             ${badge_star}
             ${badge_age}
             ${badge_dead}

             <div class="d-flex">
               ${img_text}

               <div class="mx-2">
                  ${title_safe}
                  Visits:${number_of_visits}
                  Date of the last visit:${date_last_visit}
		  ${link_text}
               </div>
             </div>
         </a>
    `;
    return text;
}


function getEntryRelatedBar(entry, from_entry_id) {
    let link_absolute = entry.link_absolute;
    let id = entry.id;
    let title = entry.title;
    let title_safe = getEntryTitleSafe(entry);
    let link = entry.link;
    let thumbnail = entry.thumbnail;
    let source__title = entry.source__title;
    let date_published = getEntryDatePublished(entry);

    let badge_text = getEntryVotesBadge(entry, true);
    let badge_star = getEntryBookmarkBadge(entry, true);
    let badge_age = getEntryAgeBadge(entry, true);
    let badge_dead = getEntryDeadBadge(entry, true);

    let img_text = '';
    if (view_show_icons) {
        const iconClass = view_small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }
    let link_text = getEntryLinkText(entry);

    let text = `
         <a
         class="list-group-item list-group-item-action"
         href="${link_absolute}?from_entry_id=${from_entry_id}" title="${title}">
             ${badge_text}
             ${badge_star}
             ${badge_age}
             ${badge_dead}

             <div class="d-flex">
               ${img_text}

               <div class="mx-2">
		  <div>
        	  ${title_safe}
		  ${link_text}
		  </div>
               </div>
             </div>
         </a>
    `;
    return text;
}


function getEntryReadLaterBar(entry) {
    let remove_link = "{% url 'rsshistory:read-later-remove' 1017 %}".replace("1017", entry.id);

    let link_absolute = entry.link_absolute;
    let id = entry.id;
    let title = entry.title;
    let title_safe = entry.title_safe;
    let link = entry.link;
    let thumbnail = entry.thumbnail;
    let source__title = entry.source__title;
    let date_published = entry.date_published.toLocaleString();

    let badge_text = getEntryVotesBadge(entry, true);
    let badge_star = getEntryBookmarkBadge(entry, true);
    let badge_age = getEntryAgeBadge(entry, true);
    let badge_dead = getEntryDeadBadge(entry, true);

    let img_text = '';
    if (view_show_icons) {
        const iconClass = view_small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }
    let link_text = getEntryLinkText(entry);

    let text = `
         <div 
         class="list-group-item list-group-item-action"
	 >
             ${badge_text}
             ${badge_star}
             ${badge_age}
             ${badge_dead}

             <div class="d-flex">
	         <a href="${link_absolute}" title="${title}" class="d-flex">
		   ${img_text}
        
                   <div class="mx-2">
		      <div>
        	         ${title_safe}
			 ${link_text}
		      </div>
        	   </div>
	         </a>
        
                 <a id="${id}" class="remove-button ms-auto" href="${remove_link}" >
                    <img src="{% static 'rsshistory/icons/icons8-trash-100.png' %}" class="content-icon" />
                 </a>
             </div>
         </div>
    `;
    return text;
}
