#### Refactor: Phase 04.06 - Menu Consolidation

**Overview** 

Review, refactor and consolidate Menus and Widgets.

**Notes**

- Menus are in need of enumeration and formal induction into the application semantics.
- Extensive use of duck-typing in app.game.menus.modules.layout. Inconsistent use of enums. Lots of math calculations that look prime for Cythonization.

{% if specification | required_for_phase %}
##### Specification

{{ specification }}

{% endif %}

{% if grooming %}
##### Architectural Analysis {{ grooming.iteration | roman_numerals }}

{{ grooming.analysis }}

{% endif %}

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
* [] Subtask: {{ subtask.description }}
{% endfor %}

{% endfor %}
{% endraw %}

