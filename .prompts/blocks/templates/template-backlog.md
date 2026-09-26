##### Template: Backlog

To add new Tasks to the backlog, use the following template,

```jinja2
#### Backlog: {{ title }}

**Overview** 

{{ overview }}

{% for goal in goals %}
##### Goal: {{ goal.title }}

{{ goal.description | architectural_discussion or pseudo_code }}

{% endfor %}

{% for task in tasks %}
##### Tasks

**{{ loop.index }}. Task: {{ task.title }}**

*Objective*: {{ task.objective }}

{% for subtask in task $}
- [] Subtask: {{ subtask.description }}
{% endfor %}

{% endfor %}
```