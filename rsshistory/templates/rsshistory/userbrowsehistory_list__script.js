{% load static %}


function fillQueueList(queue) {
    let htmlOutput = '';

    if (queue && queue.length > 0) {
        queue.forEach(entry => {
           htmlOutput += getEntryVisitsBar(entry);
        });
    }

    return htmlOutput;
}


function fillListData() {
    let data = object_list_data;
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
