**Guideline: Docstrings**

Use the following template to create docstrings for Python modules,

```jinja2
{% raw %}
{% for tag in module.tags % }
@{{ tag }}
{% endfor %}

# Ontology: Source -  {{ module.path }}

{{ module.description }}
{% endraw %}
```

**All** module docstrings must be marked with atleast one `@tag` on the very first line. They may optionally have more than one `@tag` on subsequent new lines after the first `@tag`. Tags are meant to capture logically related slices of the Application.

* Tags:
    * Domain Tags:
        * `domain.abstract`
        * `domain.concrete`
        * `domain.graphics`
        * `domain.logic`
        * `domain.model`
        * `domain.system`
        * `domain.user`
    * Predicate Tags:
        * Hierarchy Tags:
            * Asset Tags:
                * `asset.animation`
                * `asset.frame`
                * `asset.hitbox`
                * `asset.property`
                * `asset.state`
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
                * `app.component`
                * `app.config`
                * `app.devices`
                * `app.mechanics`
                * `app.module`
                * `app.schema`
                * `app.semantics`
                * `app.services`
            * Main Tags
                * `main.cli`
                * `main.hydration`
                * `main.injection`
            * Physics Tags:
                * `physics.fields`
                * `physics.motion`
                * `physics.space`
            * Workflow Tags: 
                * `workflow.collisions`
                * `workflow.combat`
                * `workflow.compositions`
                * `workflow.ecology`
                * `workflow.generation`
                * `workflow.gravity`
                * `workflow.fluids`
                * `workflow.intentions`
                * `workflow.menus`
                * `workflow.initialization`
                * `workflow.navigation`
                * `workflow.plot`
                * `workflow.rendering`
                * `workflow.seasons`
                * `workflow.telemetry`
                * `workflow.typography`


