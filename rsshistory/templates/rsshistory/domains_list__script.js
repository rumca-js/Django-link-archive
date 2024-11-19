{% load static %}

function getDomainTemplate(domain, show_icons = true, small_icons = false) {
    var id = domain.id;
    var domain_only = domain.domain;
    var main = domain.main;
    var subdomain = domain.subdomain;
    var suffix = domain.suffix;
    var tld = domain.tld;

    var url_absolute = "{% url 'rsshistory:domain-detail' 1007 %}";
    url_absolute = url_absolute.replace("1007", domain.id);

    var title = domain.domain;

    var template = `
        <a href="${url_absolute}"
           class="my-1 p-1 list-group-item list-group-item-action"
           title="${title}">
            <span class="link-list-item-title">
                ${title}
            </span>
        </a>
    `;

    return template;
}

function fillDomainList(domains) {
    let htmlOutput = '';

    if (domains && domains.length > 0) {
        domains.forEach(domain => {
            var template_text = getDomainTemplate(domain, view_show_icons, view_small_icons);
            htmlOutput += template_text;
        });
    }

    return htmlOutput;
}

function fillListData(data) {
    $('#listData').html("");

    let domains = data.domains;

    if (!domains || domains.length == 0) {
        $('#listData').html("No domains found");
        $('#pagination').html("");
        return;
    }

    var finished_text = fillDomainList(domains);
    $('#listData').html(finished_text);
    let pagination = fillPagination(data);
    $('#pagination').html(pagination);
}

{% include "rsshistory/javascript_list_utilities.js" %}
