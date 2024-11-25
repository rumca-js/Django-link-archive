{% load static %}


function sendClearList(attempt = 1) {
    let url = "{% url 'rsshistory:read-later-clear' %}";

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
          $("#listStatus").html("Successful");
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
          loadRowListContent();
          getIndicators();
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               sendClearList(attempt + 1);
               if (errorInHtml) {
                   $("#listStatus").html("Error during clear, retry");
               }
           } else {
               if (errorInHtml) {
                   $("#listStatus").html("Error during clear");
                   $('#clear-list').prop("disabled", false);
                   $('.remove-button').prop("disabled", false);
               }
           }
       }
    });
}


function sendRemoveListItem(id, attempt = 1) {
    let url = "{% url 'rsshistory:read-later-remove' 1017 %}";
    url = url.replace("1017", id);

    $.ajax({
       url: url,
       type: 'GET',
       timeout: 10000,
       success: function(data) {
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
          loadRowListContent();
          getIndicators();
       },
       error: function(xhr, status, error) {
           if (attempt < 3) {
               sendRemoveListItem(attempt + 1);
               if (errorInHtml) {
                   $("#listStatus").html("Error when removing, retry");
               }
           } else {
               if (errorInHtml) {
                   $("#listStatus").html("Error when removing");
                   $('#clear-list').prop("disabled", false);
                   $('.remove-button').prop("disabled", false);
               }
           }
       }
    });
}


function fillQueueListElement(entry) {
    let remove_link = "{% url 'rsshistory:read-later-remove' 1017 %}".replace("1017", entry.id);

    let link_absolute = entry.link_absolute;
    let id = entry.id;
    let title = entry.title;
    let title_safe = entry.title_safe;
    let link = entry.link;
    let thumbnail = entry.thumbnail;
    let source__title = entry.source__title;
    let date_published = entry.date_published.toLocaleString();

    let img_text = '';
    if (view_show_icons) {
        const iconClass = view_small_icons ? 'icon-small' : 'icon-normal';
        img_text = `<img src="${thumbnail}" class="rounded ${iconClass}" />`;
    }
    
    let thumbnail_text = '';
    if (img_text) {
        thumbnail_text = `
            <div style="position: relative; display: inline-block;">
                ${img_text}
            </div>`;
    }

    let text = `
        <div class="my-1">
         <a href="${link_absolute}" title="${title}">
             <div class="d-flex">
		 ${thumbnail_text}
        
        	 <div>
        	     ${title_safe}
        
        	     <a id="${id}" class="remove-button" href="${remove_link}">
        		<img src="{% static 'rsshistory/icons/icons8-trash-100.png' %}" class="content-icon" />
        	     </a>
        	 </div>
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
    let pagination = GetPaginationNav(data);
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
