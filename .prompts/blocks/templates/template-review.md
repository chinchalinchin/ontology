
### Template: Code Review

For reviews and critiques, use the following template,

```jinja2
{% raw %}
#### Review: {{ title }}

##### Overview

{{ overview }}

{% if necessary(review(implementation)) %}
##### Review: Implementation

{{ review(implementation) | criteria: specification met, edge cases handled }}

{% endif %}

{% if necessary(review(quality)) %}
##### Review: Quality

{{ review(quality) | criteria: omments, docstrings, code smells, constraint violations, readability }}

{% endif %}

{% if necessary(review(logic)) %}
##### Review: Logic

{{ review(logic) | criteria: inconsistencies, contradictions, ambiguities, unnecessary complexity }}

{% endif %}

{% if necessary(review(architecture)) %}
##### Review: Architecture

{{ review(architecture) | redundancies, inefficiencies, data models}}

{% endif %}

{% if necessary(review(optimization)) %}
##### Review: Optimization

{{ review(optimization) | critera: cython candidates, bottle necks, garbage collection }}

{% endif %}
{% endraw %}
```

