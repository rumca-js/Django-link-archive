{% load static %}


function fillQueueListElement(entry) {
    let link_absolute = entry.link_absolute;
    let id = entry.id;
    let title = entry.title;
    let title_safe = entry.title_safe;
    let link = entry.link;
    let thumbnail = entry.thumbnail;
    let source__title = entry.source__title;
    let date_published = entry.date_published.toLocaleString();

    let date_last_visit = entry.date_last_visit.toLocaleString();
    let number_of_visits = entry.number_of_visits;

    let img_text = '';
    if (view_show_icons) {
        const iconClass = view_small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }

    let text = `
        <div class="my-1">
         <a href="${link_absolute}" title="${title}">
             <div class="d-flex">
             ${img_text}
        
        	 <div>
        	     ${title_safe}
                 Visits:${number_of_visits}
                 Date of the last visit:${date_last_visit}
        	 </div>
         </a>
        </div>
    `;
    return text;
}

function fillQueueList(queue) {
    let htmlOutput = '';

    if (queue && queue.length > 0) {
        queue.forEach(entry => {
	   htmlOutput += fillQueueListElement(entry);
	});
    }

    return htmlOutput;
}

function fillListData(data) {
    $('#listData').html("");

    let queue = data.queue;

    if (!queue || queue.length == 0) {
        $('#listData').html("Queue is empty");
        $('#pagination').html("");
        return;
    }

    var finished_text = fillQueueList(queue);
    $('#listData').html(finished_text);
    let pagination = fillPagination(data);
    $('#pagination').html(pagination);
}


$(document).on("click", '#clear-list', function(e) {
    e.preventDefault();

    $('#clear-list').prop("disabled", true);
    $('.remove-button').prop("disabled", true);
    sendClearList();
});


$(document).on("click", '.remove-button', function(e) {
    e.preventDefault();

    $('#clear-list').prop("disabled", true);
    $('.remove-button').prop("disabled", true);

    const buttonId = $(this).attr('id');
    sendRemoveListItem(buttonId);
});

{% include "rsshistory/javascript_list_utilities.js" %}
