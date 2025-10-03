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
      let source_link = "{% url 'rsshistory:sources' %}";

      if (data.status) {
        $("#buttonsSpace").hide();
        $("#config-line").html(`${success_icon} Configuring... OK`);

         $("#setupSpace").append(`
	    <p>You can start by adding sources <a href=${source_link}>Sources</a></p>
            <p>You can enable list blocks filter domains using easy list, etc.</p>`);
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
