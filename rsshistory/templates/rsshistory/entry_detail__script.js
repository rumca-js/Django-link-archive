{% load static %}

<script>
    function loadIsEntryDownloaded(attempt = 1) {
        $.ajax({
            url: "{% url 'rsshistory:is-entry-download' object.id %}",
            type: 'GET',
            timeout: 15000,
            success: function(data) {
                if (data.status) {
                    const text = '<span class="bg-warning text-dark"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Downloading...</span>';
                    $('#entryDownloadLine').html(text);
                }
            },
            error: function(xhr, status, error) {
                if (attempt < 3) {
                    loadIsEntryDownloaded(attempt + 1);
                }
            }
        });
    }

    function loadEntryDynamicDetails(attempt = 1) {
        getDynamicContent("{% url 'rsshistory:get-entry-details' object.id %}", "#bodyBlock", 1, true);
    }

    function getDynamicJsonContentWithRefresh(url_address, htmlElement, attempt = 1, errorInHtml = false) {
        $.ajax({
           url: url_address,
           type: 'GET',
           timeout: 10000,
           success: function(data) {
              $(htmlElement).html(data.message);

              if (data.status) {
                 loadEntryMenuContent();
                 loadMenuContent();
              }
           },
           error: function(xhr, status, error) {
               if (attempt < 3) {
                   getDynamicJsonContent(url, htmlElement, attempt + 1, errorInHtml);
                   if (errorInHtml) {
                       $(htmlElement).html("Error loading dynamic content, retry");
                   }
               } else {
                   if (errorInHtml) {
                       $(htmlElement).html("Error loading dynamic content");
                   }
               }
           }
        });
    }

    function getVoteEditForm() {
        getDynamicContent('{% url "rsshistory:entry-vote-form" object.id %}', "#entryVoteLine", 1, true);
    }

    function getTagEditForm() {
      getDynamicContent('{% url "rsshistory:entry-tag-form" object.id %}', "#entryTagContainer", 1, true);
    }

    function loadEntryMenuContent() {
        getDynamicContent("{% url 'rsshistory:get-entry-menu' object.id %}", "#entryMenu", 1, true);
    }

    $(document).on('click', '#Vote', function(event) {
        event.preventDefault();
        getVoteEditForm();
    });
    $(document).on('click', '#Bookmark', function(event) {
        event.preventDefault();
        getDynamicJsonContentWithRefresh("{% url 'rsshistory:entry-bookmark' object.id %}", '#entryStatusLine');
        $('#editTagsButton').show();
    });
    $(document).on('click', '#Unbookmark', function(event) {
        event.preventDefault();
        getDynamicJsonContentWithRefresh("{% url 'rsshistory:entry-unbookmark' object.id %}", '#entryStatusLine');
        $('#editTagsButton').hide();
    });
    $(document).on('click', '#Read-later', function(event) {
        event.preventDefault();
        getDynamicJsonContentWithRefresh("{% url 'rsshistory:read-later-add' object.id %}", '#entryStatusLine');
    });
    $(document).on('click', '#Do-not-read-later', function(event) {
        event.preventDefault();

        getDynamicJsonContentWithRefresh("{% url 'rsshistory:read-later-remove' object.id %}", '#entryStatusLine');
    });
    $(document).on('click', '#Remove', function(event) {
        event.preventDefault();

        getDynamicJsonContent("{% url 'rsshistory:entry-remove' object.id %}", "#entryStatusLine");
    });


    $(document).on('submit', '#voteEditForm', function(event) {
        event.preventDefault();

        var voteData = $('#id_vote').val();

        $.ajax({
            url: "{% url 'rsshistory:entry-vote' object.id %}",
            type: 'POST',
            timeout: 10000,
            data: {
                vote: voteData,
                csrfmiddlewaretoken: '{{ csrf_token }}'
            },
            dataType: 'json',
            success: function(response) {
                if (response.status === true) {
                    $('#entryStatusLine').html("Vote added: " + response.vote);
                    $('#entryVoteLine').html("");
                } else {
                    $('#entryStatusLine').html(`<p class="text-danger">Error: ${response.message}</p>`);
                }
            },
            error: function(xhr, status, error) {
                $('#entryStatusLine').html(`<p class="text-danger">Error during vote update: ${error}</p>`);
            },
        });
    });

    $(document).on('click', '#cancelVoteEdit', function() {
        $('#entryVoteLine').html("");
    });

    $(document).on('submit', '#tagEditForm', function(event) {
      event.preventDefault();

      var tagsData = $('#id_tag').val();
      const editButton = `<button id="editTagsButton"><img src="{% static 'rsshistory/icons/icons8-edit-100.png' %}" class="content-icon" /></button>`;

      $.ajax({
        url: '{% url "rsshistory:entry-tag" object.id %}',
        type: 'POST',
        timeout: 10000,
        data: {
          tags: tagsData,
          csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        dataType: 'json',
        success: function(response) {
          if (response.status === true) {
            var tagsLinks = response.tags.map(function(tag) {
              return `<a href="{% url 'rsshistory:entries' %}?search=tags__tag+%3D%3D+${tag}">#${tag}</a>`;
            }).join(', ');

            $('#entryTagContainer').html(`${tagsLinks} ${editButton}`);
          } else {
            $('#entryTagContainer').html(`<p class="text-danger">Failed to update tags. Please try again. ${editButton}</p>`);
          }
        },
        error: function(xhr, status, error) {
          $('#entryTagContainer').html(`<p class="text-danger">Error during tag update. Please try again. ${editButton}</p>`);
        },
      });
    });

    $(document).on('click', '#editTagsButton', function() {
      getTagEditForm();
      $(this).hide();
    });

    $(document).on('click', '#cancelTagEdit', function() {
      $('#entryTagContainer').html(`
        {% if object.has_tags %}
          {% for tag in object.get_tag_map %}
            <a href="{% url 'rsshistory:entries' %}?search=tags__tag+%3D%3D+{{tag}}">#{{tag}}</a>,
          {% endfor %}
        {% endif %}
        <button id="editTagsButton"><img src="{% static 'rsshistory/icons/icons8-edit-100.png' %}" class="content-icon" /></button>
      `);
    });

    loadEntryDynamicDetails();
    loadIsEntryDownloaded();

    setInterval(function() {
        loadIsEntryDownloaded();
    }, 300000);
</script>