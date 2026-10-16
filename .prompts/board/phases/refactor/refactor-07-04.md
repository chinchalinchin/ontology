#### Refactor: Phase 07.04 - Materialization

**Overview** 

- Reduce the Strut overhead and asset proliferation by affecting a simplification through hierarchical organization of Struts via `material` and `purpose`.

**Notes**

- Determine which Assets need pruned to ensure all conform to the schema and simplify the amount of boilerplate.
- Many assets will need edited so their dimensions align along the `material` axis, or else MaterialHitbox will need introduced so segregate hitboxes by `material`.

##### Specification

- Materials: Enumeration of all game materials.
- MaterialFrame: Index Assets by material columns.
- PropertyState: `material` and `purpose` definition and specification. Logic handling.

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

