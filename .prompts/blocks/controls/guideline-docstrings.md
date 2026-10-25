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
        * `domain.abstract` (*Abstract Interfaces*)
        * `domain.concrete` (*Implementations*)
        * `domain.graphics` (*SDL & Rendering*)
        * `domain.logic` (*Algorithms*)
        * `domain.model` (*Data Structures*)
        * `domain.system` (*Support Systems*)
        * `domain.user` (*User Interfaces*)
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
            * Modality Tags
                * `modality.material`
        * Source Tags:
            * Application Tags:
                * `app.base` (*Base Implementations*)
                * `app.core` (*Core Implementations*)
                * `app.component` (*Engine Subsystems*)
                * `app.config`
                * `app.devices`
                * `app.library` (*Cython Libraries*)
                * `app.mechanics`
                * `app.module` (*Static Logical Modules*)
                * `app.schema`
                * `app.semantics` (*Application Terminology*)
                * `app.services`
            * Main Tags
                * `main.cli` 
                * `main.hydration` (*State Migration*)
                * `main.injection` (*Dependency Injection Pipeline*)
            * Physics Tags:
                * `physics.fields` (*Vector Fields*)
                * `physics.motion` (*Kinematics, Momentum, Collisions*)
                * `physics.space` (*Spatial Grid Hashing*)
            * Workflow Tags: 
                * `workflow.collisions`
                * `workflow.combat`
                * `workflow.compositions`
                * `workflow.ecology`
                * `workflow.generation` (*Procedural Generation*)
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


