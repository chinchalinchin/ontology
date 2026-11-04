**Guideline: Docstrings**

Use the following template to create docstrings for Python modules,

```jinja2
{% raw %}
{% for t in module.tags % }
@{{ t.tag }}.{{ t.name }}
{% endfor %}

{% set title = 'Source' if module.src else 'Tests' %}
# Ontology: {{ title }} -  {{ module.path }}

{{ module.description }}
{% endraw %}
```

Tags are meant to capture logically related slices of the Application.

**All** module docstrings must be marked with atleast one `@<tag>.<name>` on the very first line. They may optionally have more than one `@<tag>.<name>` on subsequent new lines after the first `@<tag>.<name>`. 

* Tags:
    * `app`: Every file should have an Application Tag.
    * `domain`: Every file should have a Domain Tag.
    * `asset`: Asset Tags are restricted to models, implementations and configurations surrounding the Asset class.
    * `category`: Category Tags are restricted to Asset Component implementations and models of a specific Category.
    * `menu`: Menu Tags are restricted to user interface systems.
    * `modality`: Modality Tags are restricted to the systems that implement the logic to differentiate the various Asset Modalities. 
    * `physics`: Physics Tags are restricted to the systems that interface with the Engine's physical calculations.
    * `test`:  Test Tags are restricted to unit tests, integration tests and exploratory tests.
    * `workflow`: Workflow Tags are restricted to Application Mechanics, modules and other logical processes that execute every Engine Loop.
* Names:
    * Domain Names:
        * `domain.abstract` (*Abstract Interfaces*)
        * `domain.automata` (*Finite State Automata*)
        * `domain.concrete` (*Abstract Implementations*)
        * `domain.logic` (*Algorithms*)
        * `domain.model` (*Data Structures*)
        * `domain.system` (*Support Systems*)
        * `domain.test` (*Test Beds*)
        * `domain.user` (*User Interfaces*)
    * Predicate Names:
        * Hierarchy Names:
            * Asset Component Names:
                * `asset.animation`
                * `asset.frame`
                * `asset.hitbox`
                * `asset.property`
                * `asset.state`
            * Asset Category Name:
                * `category.crafts`
                * `category.cursors`
                * `category.effects`
                * `category.fonts`
                * `category.geography`
                * `category.objects`
                * `category.resources`
                * `category.sheets`
                * `category.tiles`
                * `category.widgets`
            * Asset Modality Names
                * `modality.action`
                * `modality.auditory`
                * `modality.appearance`
                * `modality.frequency`
                * `modality.lifespan`
                * `modality.intention`
                * `modality.material`
                * `modality.mass`
        * Source Names:
            * Application Names:
                * `app.asset` (*Asset Implementations*)
                * `app.base` (*Base Application Implementations*)
                * `app.board` (*Application Board Database*)
                * `app.core` (*Core Application Systems*)
                * `app.component` (*Application Subsystems*)
                * `app.config`
                * `app.device` (*Input Devices*)
                * `app.library` (*Cython Libraries*)
                * `app.menu`
                * `app.mechanic` (*Mechanic Implementations*)
                * `app.module` (*Static Logical Modules*)
                * `app.schema`
                * `app.semantics` (*Application Terminology*)
                * `app.service`
                * `app.relation`
            * Menu Tags
                * `menu.binding`
                * `menu.controller`
                * `menu.handler`
            * Physics Names:
                * `physics.fields` (*Vector Fields*)
                * `physics.motion` (*Kinematics, Momentum, Collisions*)
                * `physics.space` (*Spatial Grid Hashing*)
            * Test Names:
                * `test.config`
                * `test.fixtures`
                * `test.unit`
                * `test.integration`
            * Workflow Names: 
                * `workflows.cli`
                * `workflow.cognition`
                * `workflow.collisions`
                * `workflow.combat`
                * `workflow.compositions`
                * `workflow.ecology`
                * `workflow.fluids`
                * `workflow.generation` (*Procedural Generation*)
                * `workflow.geology`
                * `workflow.gravity`
                * `workflow.hydration` (*Initialization*)
                * `workflow.interactions`
                * `workflow.main` (*Entrypoint*)
                * `workflow.injection` (*Dependency Injection Pipeline*)
                * `workflow.navigation` (*RRT Algorithms*)
                * `workflow.player`
                * `workflow.plots`
                * `workflow.rendering`
                * `workflow.seasons`
                * `workflow.telemetry`
                * `workflow.transitions`: (*Transition Translation and Execution*)
                * `workflow.typography`


