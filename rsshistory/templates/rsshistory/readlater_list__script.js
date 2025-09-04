{% load static %}


function sendClearList(attempt = 1) {
    jsonReadLaterClear(function(data) {
       if (data.status) {
          $("#listStatus").html("Successful");
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
          performSearch();
          getIndicators();
       }
       else {
          $("#listStatus").html("Error during clear");
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
       }
    });
}


function sendRemoveListItem(entry_id, attempt = 1) {
    jsonReadLaterRemove(entry_id, function() {
       if (data.status) {
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
          performSearch();
          getIndicators();
       }
       else {
          $("#listStatus").html("Error when removing");
          $('#clear-list').prop("disabled", false);
          $('.remove-button').prop("disabled", false);
       }
    });
}


function fillQueueList(queue) {
    let htmlOutput = '';

    if (queue && queue.length > 0) {
        queue.forEach(entry => {
           entry.remove_link = "{% url 'rsshistory:json-read-later-remove' 1017 %}".replace("1017", entry.id);
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

