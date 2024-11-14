{% load static %}
<script>
    function getTemplate(job) {
        let link_affected_text = "";
        if (job.link_affected) {
            let link_affected = job.link_affected;
            link_affected_text = `
           <div>
              <a href="${link_affected}" class="btn btn-secondary btn-sm mb-2" role="button">Object</a>
           </div>
           `;
        }

        let disable_link = "{% url 'rsshistory:backgroundjob-disable' 1017 %}".replace("1017", job.id);
        let enable_link = "{% url 'rsshistory:backgroundjob-enable' 1017 %}".replace("1017", job.id);
        let prio_up = "{% url 'rsshistory:backgroundjob-prio-up' 1017 %}".replace("1017", job.id);
        let prio_down = "{% url 'rsshistory:backgroundjob-prio-down' 1017 %}".replace("1017", job.id);
        let job_remove = "{% url 'rsshistory:backgroundjob-remove' 1017 %}".replace("1017", job.id);
        let jobs_remove = "{% url 'rsshistory:backgroundjobs-remove' 1017 %}".replace("1017", job.job);

        let text = `
        <div class="my-1 p-1 list-group-item list-group-item-action"
           title="${job.date_created} ${job.job} ${job.task} ${job.subject} ${job.args}">
           <div>
              ${job.id}

              [${job.date_created}] 

              ${!job.enabled ? '[DISABLED]' : ''}

              ${job.priority} <b>${job.job}</b>

              ${job.subject}

              ${job.user}

              ${job.args}
           </div>

           ${link_affected_text}

           <div>
              <a href="${disable_link}" class="btn btn-secondary btn-sm" role="button" title="Disable job">
                  {% include "rsshistory/icon_disable.html" %}
              </a>
              <a href="${enable_link}" class="btn btn-secondary btn-sm" role="button" title="Enable job">
                  {% include "rsshistory/icon_enable.html" %}
              </a>

              <a href="${prio_up}" class="btn btn-secondary btn-sm" role="button" title="Increase priority">
                 <img src="{% static 'rsshistory/icons/icons8-up-100.png' %}" class="content-icon" />
              </a>
              <a href="${prio_down}" class="btn btn-secondary btn-sm" role="button" title="Decrease priority">
                 <img src="{% static 'rsshistory/icons/icons8-down-100.png' %}" class="content-icon" />
              </a>

              <a href="${job_remove}" class="btn btn-secondary btn-sm" role="button" title="Remove job">
                 {% include "rsshistory/icon_remove.html" %}
              </a>
              <a href="${jobs_remove}" class="btn btn-secondary btn-sm" role="button" title="Remove all in type">
                 <img src="{% static 'rsshistory/icons/icons8-trash-multiple-100.png' %}" class="content-icon" />
                 Type
              </a>
           </div>
        </div>`;

        return text;
    }

    function fillJobsList(jobs) {
        let htmlOutput = '';

        if (jobs && jobs.length > 0) {
            jobs.forEach(job => {
                let date_created = new Date(job.date_created);
                if (isNaN(date_created)) {
                    date_created = new Date();
                }

                let template_text = getTemplate(job);

                // Replace placeholders globally
                const listItem = template_text
                    .replace(/\${job.id}/g, job.id)
                    .replace(/\${job.date_created}/g, date_created.toLocaleString())
                    .replace(/\${job.job}/g, job.job)
                    .replace(/\${job.subject}/g, job.subject)
                    .replace(/\${job.args}/g, job.args || '')
                    .replace(/\${job.priority}/g, job.priority || '')
                    .replace(/\${job.link_affected}/g, job.link_affected || '')
                    .replace(/1017/g, job.id)
                    .replace(/1018/g, job.job)
                    .replace(/\${job.user}/g, job.user || '');

                htmlOutput += listItem;
            });
        } else {
            htmlOutput = '<li class="list-group-item">No entries found</li>';
        }

        return htmlOutput;
    }

    function fillListData(data) {
        $('#listData').html("");

        let jobs = data.jobs;

        if (!jobs || jobs.length == 0) {
            $('#listData').html("No jobs found");
            $('#pagination').html("");
            return;
        }

        var finished_text = fillJobsList(jobs);
        $('#listData').html(finished_text);
        let pagination = fillPagination(data);
        $('#pagination').html(pagination);
    }

    {% include "rsshistory/javascript_list_utilities.js" %}

</script>
