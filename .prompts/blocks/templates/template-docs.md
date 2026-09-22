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