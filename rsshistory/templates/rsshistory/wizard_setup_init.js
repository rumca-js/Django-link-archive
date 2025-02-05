{% load static %}

function getSpinnerContainer(text = '') {
   return `<span class="spinner-container"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}</span>`;
}

function getSuccessIcon() {
  return "✔";
}

function getErrorIcon() {
  return "❌";
}

function initializeSources(button_element, button_text) {
  let spinner_container = getSpinnerContainer();
  let success_icon = getSuccessIcon();
  let error_icon = getErrorIcon();

  let source_link = "{% url 'rsshistory:sources' %}";

  $("#setupSpace").append(`<p id="source-line">${spinner_container} Creating sources...</p>`);

  $.ajax({
    url: "{% url 'rsshistory:sources-initialize' %}",
    type: "GET",
    success: function(response, status, xhr) {
      if (xhr.status === 200) {
        $("#source-line").html(`${success_icon} Creating sources... OK`);

        $("#setupSpace").append(`<p>You can enable some sources <a href=${source_link}>Sources</a></p>`);
      }
    },
    error: function() {
      $("#source-line").html(`${error_icon} Creating sources... ERROR`);
    },
    complete: function() {
      $(button_element).prop("disabled", false).html(button_text);
    }
  });
}

function setupFor(url, button_element, button_text) {
  $(button_element).prop("disabled", true);

  $(button_element).html(
    `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`
  );

  let spinner_container = getSpinnerContainer();
  let success_icon = getSuccessIcon();
  let error_icon = getErrorIcon();

  $("#setupSpace").append(`<p id="config-line">${spinner_container} Configuring...</p>`);

  $.ajax({
    url: url,
    type: "GET",
    success: function(response, status, xhr) {
      if (xhr.status === 200) {
        $("#buttonsSpace").hide();
        $("#config-line").html(`${success_icon} Configuring... OK`);
        initializeSources(button_element, button_text);
      }
    },
    error: function() {
      $("#config-line").html(`${error_icon} Configuring... ERROR`);
    },
    complete: function() {
      $(button_element).prop("disabled", false).html(button_text);
    }
  });
}

$("#btnFetchNews").click(function() {
 setupFor("{% url 'rsshistory:wizard-setup-news' %}", "#btnFetchNews", "Setup News Reader");
});
$("#btnFetchGallery").click(function() {
 setupFor("{% url 'rsshistory:wizard-setup-gallery' %}", "#btnFetchGallery", "Setup Gallery Viewer");
});
$("#btnFetchSearchEngine").click(function() {
 setupFor("{% url 'rsshistory:wizard-setup-search-engine' %}", "#btnFetchSearchEngine", "Setup Simple Search Engine");
});
