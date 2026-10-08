
#### Ontology: Task Templates

The templates in this section can be used to modify the Task Board or file reports.

##### Template: Bug Report

For ancillary or tangential bugs detected, use the following template to open new reports,

```jinja2
{% for bug in bugs %}
##### Bug {{ bug.id }}: {{ bug.title }}

**STATUS**: OPEN
**SEVERITY**: {{ bug.severity }}

**Description**

{{ bug.description }}

{% if is_reproducible(bug) %}
**Steps to Replicate** 

{{ bug.steps }}
{% endif %}

**Proposed Remeditation**

{{ remediation }}

{% endfor %}
```

##### Template: Backlog

To add new Tasks to the backlog, use the following template,

```jinja2
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
```

##### Template: Documentation

For documentation divergences detected, use the following template,

```jinja2
#### Draft: {{ title }}

- **Page**: {{ page.file }}
- **Heading**: {{ page.heading }}

##### Drift

{{ drift.description | justification }}

##### Update

{{ update.description | markdown }}
```

##### Template: Code Review

For reviews and critiques, use the following template,

```jinja2

#### Review: {{ title }}

{% if necessary(context) %}
##### Context

- {{ context.affected_systems }}
- {{ context.initial_conditions }}
- {{ context.prior_assumptions }}
{% endif % }

{% if necessary(implementation) %}
##### Implementation Control

- {{ implementation.specification_met }}
- {{ implementation.edge_cases }}
- {{ implementation.errors_handling }}
{% endif %}

{% if necessary(quality) %}
##### Quality Control

- {{ quality.comments or quality.docstrings }}
- {{ quality.code_smells }}
- {{ quality.application_constraint_violations }}
- {{ quality.readability}}
{% endif %}

{% if necessary(optimization) %}
##### Optimization Control

- {{ optimization.cython_candidates }}
- {{ optimization.bottle_necks }}
- {{ }}
{% end if}
```