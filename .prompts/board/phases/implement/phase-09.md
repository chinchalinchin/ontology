#### Phase 09: Hydrodynamics

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