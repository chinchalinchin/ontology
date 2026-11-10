#### Template: Merge Request

For merge requests, use the following template,

```jinja2
{% raw %}
##### Merge: {{ merge.title }}

###### Overview

{{ merge.overview }}

###### Changes
{% for change in merge.changes %}
* {{ change.description}}
{% endfor %}

{% endraw %}
```

