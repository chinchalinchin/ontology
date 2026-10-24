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
    * Hierarchy Tags:
        * Asset Tags:
            * `asset.property`
            * `asset.state`
            * `asset.frame`
            * `asset.animation`
            * `asset.hitbox`
        * Category Tags:
            * `category.crafts`
            * `category.cursors`
            * `category.effects`
            * `category.geography`
            * `category.objects`
            * `category.resources`
            * `category.sheets`
            * `category.tiles`
            * `category.widgets`
    * Source Tags:
        * Application Tags:
            * `app.base`
            * `app.core`
            * `app.config`
            * `app.schema`
            * `app.semantics`
            * `app.services`
            * `app.input`
            * `app.mechanics`
        * Main Tags
            * `main.cli`
            * `main.graphics`
            * `main.hydration`
            * `main.injection`
        * Workflow Tags: 
            * `workflow.collisions`
            * `workflow.combat`
            * `workflow.compositions`
            * `workflow.ecology`
            * `workflow.generation`
            * `workflow.fluids`
            * `workflow.intentions`
            * `workflow.menus`
            * `workflow.motion`
            * `workflow.initialization`
            * `workflow.pathfinding`
            * `workflow.rendering`
            * `workflow.seasons`
            * `workflow.telemetry`
            * `workflow.typography`