#### Implement: Phase 11 - Geology

**Overview** 

- Move Obstacles into Geography. Obstacles partitioned along `material` columns in their atlas. Row indices use `formation`. 
- `formation` indicates the "geological structure". Need to enumerate.
- Introduce geological principles:
    - When two Environ Tiles meet, they form a "faultine" along their common edge. 
    - During procedural phase of Board hydration, Obstacles are generated probabilistically using the faultlines to localize probability around their locations, i.e. faultlines act as "sources" of Obstacles and they are more likely to spawn near those locations during procedural generation.
    - Additionally, principles need to be established to differentiate the generation of `geologics`.

{% if specification | required_for_phase %}
##### Specification

{{ specification }}

{% endif %}

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
* [] Subtask: {{ subtask.description }}
{% endfor %}

{% endfor %}