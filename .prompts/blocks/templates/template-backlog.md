
### Template: Backlog

To add new Tasks to the backlog, use the following template,

```jinja2
{% raw %}
#### {{ phase_action }}: {{ title }}

**Overview** 

{{ overview }}

{% if specification | required_for_phase %}
##### Specification

{{ specification }}

{% endif %}

{% if grooming %}
##### Architectural Analysis {{ grooming.iteration }}

{{ grooming.analysis }}

{% endif %}

{% if user %}
{# Reserved Block for User #}
##### User Review {{ user.iteration }}

{{ user.alignment or user.constraints or user.notes }}

{% endif }

##### Goals

{% for goal in goals %}
###### Goal: {{ goal.title }}

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
{% endraw %}
```

