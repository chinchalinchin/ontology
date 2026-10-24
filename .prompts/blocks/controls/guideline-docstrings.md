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

**All** module docstrings must be marked with a `tag` on the very first line. They may optionally have more than one tag.

* Tags: 
    * Script Tags: 
        * `script.context`
        * `script.synthesize`
    * Source Tags:
        * Main Tags
            * `main.cli`
            * `main.core`
            * `main.graphics`
        * Asset Tags:
            * `asset.base` 
            * `asset.properties`
            * `asset.state`
            * `asset.frames`
            * `asset.animations`
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