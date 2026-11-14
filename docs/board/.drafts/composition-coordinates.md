The `Decomposer` resolves coordinates during `unpack()` through a hierarchical context traversal governed by the **Layer Parity Check** in `_hydrate_state()`.

---

### Context Data Structures

`Decomposer` maintains two dictionary scopes during traversal:

1. **`root_context`**: Created once per composition deployment in `unpack()`. Contains the absolute deployed state of the root strut:

$$\text{root\_context} = \{\text{position}: (X_{\text{root}}, Y_{\text{root}}), \text{layer}: L_{\text{root}}, \dots\}$$


2. **`parent_context` (`node_context`)**: Created in `_unpack_node()` for the currently evaluated strut (root or branch). Contains the strut's resolved absolute position and layer:

$$\text{node\_context} = \{\text{position}: (X_{\text{strut}}, Y_{\text{strut}}), \text{layer}: L_{\text{strut}}, \dots\}$$



---

### The Governing Coordinate Translation Law

Whenever any entity (strut or component) is hydrated, `_hydrate_state()` determines its base reference point ($base\_pos$) by comparing the entity's target layer against its immediate parent's layer:

```python
is_cross_layer = str(kwargs.get('layer')) != str(parent_context.get('layer'))
base_pos = Position(0, 0) if is_cross_layer else parent_context['position']

pseudo_pos = kwargs.get('position')
if pseudo_pos:
    kwargs['position'] = Position(
        x=base_pos.x + pseudo_pos.x,
        y=base_pos.y + pseudo_pos.y
    )
else:
    kwargs['position'] = Position(base_pos.x, base_pos.y)

```

---

### 1. Root Strut & Its Components

#### Root Strut

* `_unpack_node()` is invoked with `parent_context = root_context`.
* Since `kwargs['layer']` is omitted or matches `root_context['layer']`, `is_cross_layer = False`.
* `base_pos = root_context['position'] = (X_{\text{root}}, Y_{\text{root}})`.
* If the root strut defines no pseudo-position, it adopts `base_pos` verbatim:

$$(X, Y)_{\text{root\_strut}} = (X_{\text{root}}, Y_{\text{root}})$$



#### Root Components

* `_unpack_components()` runs with `parent_context = node_context` of the root strut.
* **Same Layer ($L_{\text{comp}} == L_{\text{root}}$)**:
* `is_cross_layer = False` $\implies base\_pos = (X_{\text{root}}, Y_{\text{root}})$.
* Final coordinate is offset from the deployed root:

$$(X, Y)_{\text{comp}} = (X_{\text{root}} + x_{\text{pseudo}},\, Y_{\text{root}} + y_{\text{pseudo}})$$




* **Cross Layer ($L_{\text{comp}} \neq L_{\text{root}}$)**:
* `is_cross_layer = True` $\implies base\_pos = (0, 0)$.
* Final coordinate anchors strictly to the origin of the foreign layer:

$$(X, Y)_{\text{comp}} = (0 + x_{\text{pseudo}},\, 0 + y_{\text{pseudo}})$$





---

### 2. Branch Struts

In `unpack()`, branch nodes are traversed by calling `_unpack_node(branch, root_context, root_context, inc, is_root=False)`.

* The branch strut's `parent_context` is **`root_context`**.
* **Branch on Interior / Distinct Layer ($L_{\text{branch}} \neq L_{\text{root}}$)**:
* `is_cross_layer = True` because the branch layer differs from `root_context['layer']`.
* `base_pos` resets to `(0, 0)`.
* The branch strut's absolute position becomes:

$$(X, Y)_{\text{branch\_strut}} = (0 + x_{\text{branch\_pseudo}},\, 0 + y_{\text{branch\_pseudo}})$$




* **Branch on Same Layer ($L_{\text{branch}} == L_{\text{root}}$)**:
* `is_cross_layer = False`.
* `base_pos = root_context['position']`.
* The branch strut offsets from the exterior deployment position:

$$(X, Y)_{\text{branch\_strut}} = (X_{\text{root}} + x_{\text{branch\_pseudo}},\, Y_{\text{root}} + y_{\text{branch\_pseudo}})$$





---

### 3. Components of the Branch Strut

Inside `_unpack_node()` for the branch, `node_context` is constructed from the newly calculated `strut_state`:


$$\text{node\_context}[\text{"position"}] = (X, Y)_{\text{branch\_strut}}$$

$$\text{node\_context}[\text{"layer"}] = L_{\text{branch}}$$

When `_unpack_components()` iterates over the branch's component lists, `parent_context` is this `node_context`:

* **Component on Branch Layer ($L_{\text{comp}} == L_{\text{branch}}$)**:
* `is_cross_layer = False`.
* $base\_pos = (X, Y)_{\text{branch\_strut}}$.
* Final coordinate is relative to the branch strut's resolved origin:

$$(X, Y)_{\text{branch\_comp}} = (X_{\text{branch\_strut}} + x_{\text{comp\_pseudo}},\, Y_{\text{branch\_strut}} + y_{\text{comp\_pseudo}})$$



*(When the branch strut is placed at $(0, 0)$, $(X, Y)_{\text{branch\_comp}}$ equals $(x_{\text{comp\_pseudo}}, y_{\text{comp\_pseudo}})$ exactly).*


* **Component on Nested Foreign Layer ($L_{\text{comp}} \neq L_{\text{branch}}$)**:
* `is_cross_layer = True`.
* $base\_pos = (0, 0)$.
* Coordinates anchor directly to layer zero:

$$(X, Y)_{\text{branch\_comp}} = (0 + x_{\text{comp\_pseudo}},\, 0 + y_{\text{comp\_pseudo}})$$





---

### 4. Teleport Exit Coordinates (`out`)

For entities declaring teleport exits (such as `doors`), `_hydrate_state()` resolves `out` using target layer awareness rather than local parent positions:

```python
pseudo_out = kwargs.get('out')
if pseudo_out:
    outlayer = kwargs.get('outlayer')
    if str(outlayer) == str(root_layer):
        kwargs['out'] = Position(
            x=root_context['position'].x + pseudo_out.x,
            y=root_context['position'].y + pseudo_out.y
        )
    else:
        kwargs['out'] = Position(pseudo_out.x, pseudo_out.y)

```

* **Returning to Exterior (`outlayer == root_context['layer']`)**: The exit coordinate offsets by `root_context['position']`, allowing interior doors to drop the player relative to wherever the building was deployed in world space.
* **Traversing Between Interior Layers (`outlayer != root_context['layer']`)**: The exit coordinate is treated as an absolute local position on the target interior coordinate plane without adding the root world offset.