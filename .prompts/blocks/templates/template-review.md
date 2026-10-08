
### Template: Code Review

For reviews and critiques, use the following template,

```jinja2
{% raw %}
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
{% endif %}
{% endraw %}
```

