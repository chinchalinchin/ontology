### Template: Backlog

To add new Tasks to the backlog, use the following template,

```jinja2
{% raw %}
#### Design: {{ Composition | Menu }} - {{ title }}

**Overview** 

{{ overview }}

{% if property_adjustments | required_for_design %}
##### Property Adjustments

{% for adjustmnet in property_adjustments %}
**{{ loop.index }}**. {{ adjustment }}
{% endfor %}

{% endif %}


{% endraw %}
```

