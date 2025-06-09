/*
 * requires
 *  - show_pure_link
 *  - highlight_bookmarks
 */


function isEntryValid(entry) {
    return entry.is_valid;
}


function getEntryLink(entry) {
    return show_pure_links ? entry.link : entry.link_absolute;
}


function canUserView(entry) {
    if (entry.age == 0 || entry.age == null)
        return true;

    if (entry.age < user_age)
        return true;

    return false;
}


function getEntryAuthorText(entry) {
    if (entry.author && entry.album)
    {
        return entry.author + " / " + entry.album;
    }
    else if (entry.author) {
        return entry.author;
    }
    else if (entry.album) {
        return entry.album;
    }
    return "";
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


function getEntryThumbnail(entry) {
    if (!canUserView(entry))
    {
        return;
    }

    let thumbnail = entry.thumbnail;

    return thumbnail;
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
            datePublishedStr = parseDate(datePublished);
        }
    }

    return datePublishedStr;
}


function getEntryTitleSafe(entry) {
    let title_safe = "";

    if (!canUserView(entry))
    {
        return "----Age limited----";
    }

    if (entry.title_safe) {
       title_safe = escapeHtml(entry.title_safe)
    }
    else
    {
       title_safe = escapeHtml(entry.title)
    }

    if (title_safe.length > 200) {
        title_safe = title_safe.substring(0, 200);
        title_safe = title_safe + "...";
    }

    return title_safe;
}


/**
 * Detail view
 */


function EntryToArchiveOrg(entry) {
    let link = entry.link;

    let currentDate = new Date();
    let formattedDate = currentDate.toISOString().split('T')[0].replace(/-/g, ''); // Format: YYYYMMDD

    return `https://web.archive.org/web/${formattedDate}000000*/${link}`;
}


function EntryToW3CValidator(entry) {
    let link = entry.link;

    return `https://validator.w3.org/nu/?doc=${encodeURIComponent(link)}`;
}


function EntryToSchemaValidator(entry) {
    let link = entry.link;

    return `https://validator.schema.org/#url=${encodeURIComponent(link)}`;
}


function EntryToWhoIs(entry) {
    let link = entry.link;
    let domain = link.replace(/^https?:\/\//, ''); // Remove 'http://' or 'https://'

    return `https://who.is/whois/${domain}`;
}


function EntryToTranslate(entry) {
    let link = entry.link;

    let reminder = '?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=wapp';
    if (link.indexOf("http://") != -1) {
       reminder = '?_x_tr_sch=http&_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=wapp';
    }

    if (link.indexOf("?") != -1) {
        let queryParams = link.split("?")[1];
        reminder += '&' + queryParams;
    }

    let domain = link.replace(/^https?:\/\//, '').split('/')[0]; // Extract the domain part

    domain = domain.replace(/-/g, '--').replace(/\./g, '-');

    let translateUrl = `https://${domain}.translate.goog/` + reminder;

    return translateUrl;
}


function GetEditMenu(entry) {
    let link = entry.link;

    let translate_link = EntryToTranslate(entry);
    let archive_link = EntryToArchiveOrg(entry);
    let w3c_link = EntryToW3CValidator(entry);
    let schema_link = EntryToSchemaValidator(entry);
    let who_is_link = EntryToWhoIs(entry);

    let text = 
    `<div class="dropdown mx-1">
        <button class="btn btn-primary" type="button" id="#entryViewDrop" data-bs-toggle="dropdown" aria-expanded="false">
          View
        </button>
        <ul class="dropdown-menu">`;

    text += `
        <li>
          <a href="${translate_link}" id="Edit" class="dropdown-item" title="Edit entry">
             View translate
          </a>
        </li>
    `;

    text += `
        <li>
          <a href="${archive_link}" id="Archive-org" class="dropdown-item" title="View archived version on archive.org">
             View archive.org
          </a>
        </li>
    `;

    text += `
        <li>
          <a href="${w3c_link}" id="w3c-validator" class="dropdown-item" title="Edit entry">
             W3C validator
          </a>
        </li>
    `;

    text += `
        <li>
          <a href="${schema_link}" id="Schama-Validator" class="dropdown-item" title="Edit entry">
             Schema validator
          </a>
        </li>
    `;

    text += `
        <li>
          <a href="${who_is_link}" id="Who-Is" class="dropdown-item" title="Edit entry">
             Who Is validator
          </a>
        </li>
    `;

    text += `</div>`;

    return text;
}


function getEntryBodyText(entry) {
    date_published = parseDate(entry.date_published);

    let text = `
    <a href="${entry.link}"><h1>${entry.title}</h1></a>
    <div><a href="${entry.link}">${entry.link}</a></div>
    <div><b>Publish date:</b>${date_published}</div>
    `;

    let tags_text = getEntryTags(entry);
    
    text += `
        <div>Tags: ${tags_text}</div>
    `;

    text += GetEditMenu(entry);

    let description = entry.description.replace(/\n/g, '<br>');
    description = createLinks(description);

    text += `
    <div>${description}</div>
    `;

    text += `
    <h3>Parameters</h3>
    <div>Points: ${entry.page_rating}|${entry.page_rating_votes}|${entry.page_rating_contents}</div>
    `;

    if (entry.date_created) {
        date_created = parseDate(entry.date_created);
        text += `<div>Creation date:${date_created}</div>`;
    }

    if (entry.date_updated) {
        date_updated = parseDate(entry.date_updated);
        text += `<div>Update date:${date_updated}</div>`;
    }

    if (entry.date_dead_since) {
        date_dead_since = parseDate(entry.date_dead_since);
        text += `<div>Dead since:${date_dead_since}</div>`;
    }

    text += `
    <div>Author: ${entry.author}</div>
    <div>Album: ${entry.album}</div>
    <div>Status code: ${entry.status_code}</div>
    <div>Permanent: ${entry.permanent}</div>
    <div>Language: ${entry.language}</div>
    `;

    if (entry.manual_status_code) {
       text += `
       <div>Manual status code: ${entry.manual_status_code}</div>
       `;
    }

    if (entry.age) {
       text += `
       <div>Age: ${entry.age}</div>
       `;
    }

    return text;
}


function getEntryFullTextStandard(entry) {
    let text = `<div entry="${entry.id}" class="entry-detail">`;

    if (entry.thumbnail) {
       text += `
       <div><img src="" style="max-width:30%;"/></div>
       `;

       if (canUserView(entry))
       {
          text = `
          <div><img src="${entry.thumbnail}" style="max-width:30%;"/></div>
          `;
       }
    }

    text += getEntryBodyText(entry);

    text += "</div>";

    return text;
}


function getEntryFullTextYouTube(entry) {
    const urlParams = new URL(entry.link).searchParams;
    const videoId = urlParams.get("v");

    const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}` : "";

    let text = `<div entry="${entry.id}" class="entry-detail">`;

    if (videoId) {
        text += `
          <div class="youtube_player_container">
              <iframe src="${embedUrl}" frameborder="0" allowfullscreen class="youtube_player_frame" referrerpolicy="no-referrer-when-downgrade"></iframe>
          </div>
        `;
    }

    text += getEntryBodyText(entry);

    text += "</div>";

    return text;
}


function getEntryFullTextOdysee(entry) {
    const url = new URL(entry.link);
    const videoId = url.pathname.split('/').pop();

    const embedUrl = videoId ? `https://odysee.com/$/embed/${videoId}` : "";

    let text = `<div entry="${entry.id}" class="entry-detail">`;

    if (videoId) {
        text += `
           <div class="youtube_player_container">
               <iframe style="position: absolute; top: 0px; left: 0px; width: 100%; height: 100%;" width="100%" height="100%" src="${embedUrl}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen"></iframe>
           </div>
        `;
    }

    text += getEntryBodyText(entry);
    text += "</div>";

    return text;
}


function getEntryDetailText(entry) {
    let text = "";

    if (entry.link.startsWith("https://www.youtube.com/watch?v="))
        text = getEntryFullTextYouTube(entry);
    else if (entry.link.startsWith("https://odysee.com/"))
        text = getEntryFullTextOdysee(entry);
    else
        text = getEntryFullTextStandard(entry);

    return text;
}


/**
 * Entry list items
 */


function entryStandardTemplate(entry, show_icons = true, small_icons = false) {
    let page_rating_votes = entry.page_rating_votes;

    let badge_text = getEntryVotesBadge(entry);
    let badge_star = getEntryBookmarkBadge(entry);
    let badge_age = getEntryAgeBadge(entry);
    let badge_dead = getEntryDeadBadge(entry);

    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;
    let bookmark_class = entry.bookmarked ? `list-group-item-primary` : '';
    let thumbnail = getEntryThumbnail(entry);

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
    let entry_link = getEntryLink(entry);

    return `
        <a 
            href="${entry_link}"
            entry="${entry.id}"
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

    let badge_text = getEntryVotesBadge(page_rating_votes);
    let badge_star = highlight_bookmarks ? getEntryBookmarkBadge(entry) : "";
    let badge_age = getEntryAgeBadge(entry);
    let badge_dead = getEntryDeadBadge(entry);
   
    let invalid_style = isEntryValid(entry) ? `` : `style="opacity: 0.5"`;
    let bookmark_class = (entry.bookmarked && highlight_bookmarks) ? `list-group-item-primary` : '';

    let thumbnail = getEntryThumbnail(entry);

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
    let entry_link = getEntryLink(entry);
    let hover_title = title_safe + " " + tags_text;
    let link = entry.link;

    let link_text = getEntryLinkText(entry);

    return `
        <a 
            href="${entry_link}"
            entry="${entry.id}"
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

    let thumbnail = getEntryThumbnail(entry);
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
    let entry_link = getEntryLink(entry);
    let source__title = getEntrySourceTitle(entry);

    return `
        <a 
            href="${entry_link}"
            entry="${entry.id}"
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

    let thumbnail = getEntryThumbnail(entry);
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

    let entry_link = getEntryLink(entry);

    return `
        <a 
            href="${entry_link}"
            entry="${entry.id}"
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
                    {% include "rsshistory/icon_remove.html" %}
                 </a>
             </div>
         </div>
    `;
    return text;
}
