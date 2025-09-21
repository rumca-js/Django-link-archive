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

  jsonSourcesInitialize(function(data) {
      if (data.status) {
         $("#source-line").html(`${success_icon} Creating sources... OK`);
         $("#setupSpace").append(`<p>You can enable some sources <a href=${source_link}>Sources</a></p>`);
      }
      else {
         $("#source-line").html(`${error_icon} Creating sources... ERROR`);
      }
      $(button_element).prop("disabled", false).html(button_text);
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

  getDynamicJson(url, function (data) {
      if (data.status === 200) {
        $("#buttonsSpace").hide();
        $("#config-line").html(`${success_icon} Configuring... OK`);
        initializeSources(button_element, button_text);
      }
      else {
        $("#config-line").html(`${error_icon} Configuring... ERROR`);
      }
      $(button_element).prop("disabled", false).html(button_text);
  });
}

$("#btnFetchNews").click(function() {
 setupFor("{% url 'rsshistory:json-wizard-setup-news' %}", "#btnFetchNews", "Setup News Reader");
});
$("#btnFetchGallery").click(function() {
 setupFor("{% url 'rsshistory:json-wizard-setup-gallery' %}", "#btnFetchGallery", "Setup Gallery Viewer");
});
$("#btnFetchSearchEngine").click(function() {
 setupFor("{% url 'rsshistory:json-wizard-setup-search-engine' %}", "#btnFetchSearchEngine", "Setup Simple Search Engine");
});
