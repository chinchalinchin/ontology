#### Refactor: Phase 07.04 - Materialization

**Overview** 

- Reduce the Strut overhead and asset proliferation by effecting a simplification through hierarchical organization of Struts into `material`.

##### Specification

- Materials: Enumeration of all game materials.
- MaterialFrame: Index Assets by material columns.

{% if grooming %}
##### Architectural Analysis {{ grooming.iteration | roman_numerals }}

{{ grooming.analysis }}

{% endif %}

{% if user %}
{# Reserved Block for User #}
##### User Review {{ user.iteration | roman_numerals }}

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

