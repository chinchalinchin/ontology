
#### Ontology: Task Templates

The templates in this section can be used to modify the Task Board.

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

##### Template: Documentation

For documentation divergences detected, use the following template,

```
#### Draft: {{ title }}

- **Page**: {{ page.file }}
- **Heading**: {{ page.heading }}

##### Drift

{{ drift.description | justification }}

##### Update

{{ update.description | markdown }}
```