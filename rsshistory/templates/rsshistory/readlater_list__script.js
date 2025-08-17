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
          performSearch();
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
          performSearch();
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


function fillQueueList(queue) {
    let htmlOutput = '';

    if (queue && queue.length > 0) {
        queue.forEach(entry => {
           entry.remove_link = "{% url 'rsshistory:read-later-remove' 1017 %}".replace("1017", entry.id);
           entry.remove_icon = `{% include 'rsshistory/icon_remove.html' %}`;
	   htmlOutput += getEntryReadLaterBar(entry);
	});
    }

    return htmlOutput;
}


function fillListData() {
    $('#listData').html("");

    let data = object_list_data;

    let queue = data.queue;

    if (!queue || queue.length == 0) {
        $('#listData').html("Queue is empty");
        $('#pagination').html("");
        return;
    }

    var finished_text = fillQueueList(queue);
    $('#listData').html(finished_text);
    let pagination = GetPaginationNav(data.page, data.num_pages, data.count);
    $('#pagination').html(pagination);
}


{% include "rsshistory/javascript_list_utilities.js" %}


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

