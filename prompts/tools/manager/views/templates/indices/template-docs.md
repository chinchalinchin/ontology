#### Template: Documentation

For documentation divergences detected, use the following template,

```jinja2
{% raw %}
{% for page in documentation if page is drifting %}
##### Draft: {{ title }}

- **Page**: {{ page.file }}
- **Heading**: {{ page.heading }}

###### Drift

{{ page.drift.description | justification }}

###### Update

{{ page.update.description | markdown }}
{% endfor %}
{% endraw %}
```

