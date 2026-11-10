#### Template: Merge

For merge requests, use the following template,

```jinja2
{% raw %}
# Merge: {{ merge.title }}

## Merge: Overview

{{ merge.overview }}

## Merge: Changes

### Change: Models

{% for change in merge.changes.models.items %}
* {{ change.description }}
{% endfor %}

### Change: Logic

{% for change in merge.changes.logic.items  %}
* {{ change.description }}
{% endfor %}

{% if other in merge.changes %}
### Change: {{ merge.changes.other.title  }}

{% for change in merge.changes.other.items %}
* {{ change.description }}
{% endfor %}

{% endraw %}
```

