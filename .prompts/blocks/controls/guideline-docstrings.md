**Guideline: Docstrings**

Use the following template to create docstrings for Python modules,

```jinja2
{% raw %}
{% for tag in module.tags % }
@{{tag}}
{% endfor %}

# Ontology: {{ module.path }}

{{ module.description }}
{% endraw %}
```

**All** module docstrings must be marked with atleast one `@tag` on the very first line. They may optionally have more than one `@tag` on subsequent new lines after the first `@tag`.

* Tags:
    * Application Tags:
        * `app.core`
        * `app.base`
        * `app.semantics`
        * `app.input`
        * `app.mechanics`
    * Enumeration Tags:
    * Script Tags: 
        * `scripts.context`
        * `scripts.synthesize`
    * Source Tags:
        * Main Tags
            * `main.cli`
            * `main.graphics`
        * Asset Tags:
            * `asset.property`
            * `asset.state`
            * `asset.frame`
            * `asset.animation`
            * `asset.hitbox`
        * Hierarchy Tags:
            * `category.crafts`
            * `category.cursors`
            * `category.effects`
            * `category.geography`
            * `category.objects`
            * `category.resources`
            * `category.sheets`
            * `category.tiles`
            * `category.widgets`
        * Workflow Tags: 
            * `workflow.collisions`
            * `workflow.combat`
            * `workflow.compositions`
            * `workflow.ecology`
            * `workflow.fluids`
            * `workflow.intentions`
            * `workflow.menus`
            * `workflow.motion`
            * `workflow.orchestration`
            * `workflow.pathfinding`
            * `workflow.rendering`
            * `workflow.seasons`
            * `workflow.telemetry`