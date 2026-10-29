#### Refactor: Phase 07.05 - Composite Compositions

##### Architectural Overview

Because `CompositionPseudoState.components` is already typed as `StateSchema` (`src/app/models/config/compositions.py`), and `StateSchema` already declares `compositions: Optional[List[PropertyState]] = None`, **zero changes are required to the Pydantic or dataclass models** to represent compositions within compositions. A Composition can already declare nested compositions under `components.compositions`:

```yaml
components:
  compositions:
    - id: brick-house
      name: north-cottage
      position:
        x: 0
        y: 0

```

Currently, nested compositions are inert because of two filters:

1. **`CompositionCompiler._register_components()`** skips any key under `components` whose value is not a `dict` (`crafts: {struts: [...]}` is a `dict`, whereas `compositions: [...]` is a `list`).
2. **`Decomposer._unpack_components()`** skips all keys in `Shortcuts` (`if cat_key in Shortcuts: continue`), ignoring `Shortcuts.COMPOSITIONS`.

Enabling arbitrary composition nesting requires extending `CompositionCompiler` and `Decomposer` across three formal axes: **Topological DAG Compilation**, **Bounding Envelope & Hierarchical Scope Projection**, and **Recursive Superposition & Layer Isolation**.

##### Formal Specification

###### 1. Directed Acyclic Graph (DAG) & Topological Compilation

Let $\mathcal{C}$ be the set of all Composition configurations in `/src/data/config/compositions/**/*.yaml`. Define a directed edge $A \to B$ if Composition $A$ declares an entry with `id: B` inside `root.components.compositions` or `branches[*].components.compositions`.

* **Acyclicity Invariant**: $\mathcal{G} = (\mathcal{C}, E)$ must form a strict Directed Acyclic Graph (DAG). If a cycle $A \to^* A$ exists, `CompositionCompiler` must fail fast during bootstrap with a `ValueError` identifying the cycle path.
* **Bottom-Up Compilation Order**: If $A \to B$, $B$ must be compiled before $A$ so that all macro expressions inside $B$ are concrete before $A$ queries $B$'s spatial metrics (`span`, `dimensions`, or child member coordinates).

###### 2. Sub-Composition Spatial Metrics (`dimensions`, `span`, and Child Member Projection)

When Composition $A$ embeds Composition $B$ under `name: sub_comp`, siblings in $A$ need well-defined metrics when evaluating `bind(sub_comp.<path>)` and `anchor(sub_comp)`:

1. **Unit Dimensions (`sub_comp.dimensions`)**:
Inherited from $B$'s Root Strut (`B.root.strut.dimensions`).
2. **Composite Bounding Envelope (`sub_comp.span`)**:
A Composition's exterior footprint on its deployed layer is the union of its Root Strut and all same-layer Root Components (including any nested sub-compositions). For a compiled Composition $B$, its root-layer bounding envelope is:

$$W_B = \max_{u \in B_{\text{root}}} \big(u.\text{position}.x + u.\text{span}.w\big), \qquad L_B = \max_{u \in B_{\text{root}}} \big(u.\text{position}.y + u.\text{span}.l\big)$$

For example, in `brick-house`, `roof` ($96 \times 96$ at $y = 0$) and `exterior` ($96 \times 96$ at $y = 96$) yield $\text{span}(\text{brick-house}) = \text{Dimensions}(96, 192)$.
3. **Hierarchical Member Scope (`sub_comp.<child_name>.<field>`)**:
Each compiled Composition $B$ exports its `global_scopes` table. When $B$ is instantiated as `sub_comp` at local offset $(x_{\text{sub}}, y_{\text{sub}})$ inside $A$, `ScopeNode` exposes $B$'s named members as child scopes translated by $(x_{\text{sub}}, y_{\text{sub}})$ when on the root layer:

* `bind(sub_comp.span.l)` $\to 192$
* `bind(sub_comp.exterior.dimensions.l)` $\to 96$
* `anchor(sub_comp)` $\to$ aligns baseline to the southern edge of $B$'s root-layer envelope ($y_{\text{sub}} + L_B$).
* `anchor(sub_comp.exterior)` $\to$ aligns baseline to $B$'s `exterior` strut ($y_{\text{sub}} + y_{\text{exterior}} + l_{\text{exterior}}$).

###### 3. Recursive State Superposition & Layer Isolation in `Decomposer`

When `Decomposer` unpacks Composition $A$ at deployment increment $\text{inc}_A$ and encounters a nested `PropertyState` $S_B$ in `components.compositions`:

1. **Superposition**: `Decomposer._hydrate_state()` hydrates $S_B$ against $A$'s active `parent_context` and `root_context`:

* **Position**: $\text{pos}(S_B) = \text{pos}(\text{parent}_A) + \text{pos}_{\text{pseudo}}(S_B)$ if $S_B$ remains on $\text{parent}_A$'s layer, or $(0, 0) + \text{pos}_{\text{pseudo}}(S_B)$ if $S_B$ transitions to an independent layer.
* **Layer**: If $S_B.\text{layer}$ is unspecified, it inherits $\text{parent}_A.\text{layer}$ (which may be the board's exterior layer `'0'` or an already-namespaced interior branch layer of $A$, such as `'courtyard-1'`).
* **Elevation & Owner**: Inherited from $\text{parent}_A$ if unspecified on $S_B$:

$$E(S_B) = E(\text{parent}_A) + (S_B.\text{elevation} \text{ or } 0)$$

* **Hydrated Name**: Namespaced to `<comp_name>-<parent_name>-<inc_A>` so child struts and components inside $B$ inherit a full lineage trace.

2. **Recursive `unpack(hydrated_sub_state)**`:

* Calling `self.unpack(hydrated_sub_state)` allocates a fresh monotonic increment $\text{inc}_B = \text{self.\_increment}$ for $B$.
* **Automatic Multi-Instance Layer Isolation**: If Composition $A$ embeds two `brick-house` instances (`cottage-west` and `cottage-east`), `cottage-west` receives $\text{inc} = 2$ (namespacing its interior layer to `house-layer-2`) and `cottage-east` receives $\text{inc} = 3$ (namespacing its interior layer to `house-layer-3`).
* **Seamless Return Doors**: Because $B$'s `root_context["layer"]` is $S_B$'s hydrated layer and $B$'s `root_context["position"]` is $S_B$'s hydrated position, any Door inside $B$ returning to $B$'s root layer automatically deposits the Sprite back onto $A$'s layer at $\text{pos}(S_B) + \text{out}_B$.

##### Implementation Details

#### 1. `src/app/static/compiler.py`

Adds topological sorting with cycle detection across `merged_config["compositions"]`, computes each composition's root-layer bounding envelope, and registers `components.compositions` entries as composite `ScopeNode` instances with child member lookup.

```python
"""
@domain.logic
@app.config
@workflow.compositions

# Ontology: Source - app.static.compiler

Compile-time macro and algebraic expression resolver for Composition configurations.
"""
# Standard Libraries
import ast
import operator
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union
)
import logging

# Application Libraries
from app.models.properties import (
    AssetProperties,
    PropertiesSchema
)
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    MultiplicationStrategies,
    Orientations,
    Shortcuts
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------

MACRO_TOKEN_PATTERN = re.compile(r"\b(bind|anchor)\(([^()]+)\)")
SINGLE_BIND_PATTERN = re.compile(r"^bind\(([^()]+)\)$")

_BINARY_OPS: Dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_UNARY_OPS: Dict[type, Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# ---------------------------------------------------------


class ScopeNode:
    """
    Compile-time proxy for a Composition entity or nested sub-composition
    exposing its static AssetProperties, multiplied/composite span Dimensions,
    raw PseudoState dictionary, and nested child scopes.
    """
    def __init__(
        self,
        raw_state: Dict[str, Any],
        props: Optional[AssetProperties],
        span: Dimensions,
        parent_node: Optional["ScopeNode"] = None,
        root_node: Optional["ScopeNode"] = None,
        dimensions: Optional[Dimensions] = None,
        children: Optional[Dict[str, "ScopeNode"]] = None
    ):
        self._raw = raw_state
        self.properties = props
        self.dimensions = (
            dimensions
            if dimensions is not None
            else (
                props.dimensions
                if props and props.dimensions
                else Dimensions(0, 0)
            )
        )
        self.span = span
        self.parent = parent_node
        self.root = root_node
        self.children: Dict[str, ScopeNode] = children or {}

    @property
    def position(self) -> Position:
        raw_pos = self._raw.get("position")
        if not isinstance(raw_pos, dict):
            return Position(0, 0)
        x = raw_pos.get("x", 0)
        y = raw_pos.get("y", 0)
        return Position(
            int(x) if isinstance(x, (int, float)) else 0,
            int(y) if isinstance(y, (int, float)) else 0
        )


class CompiledCompositionMeta:
    """
    Stores the compiled spatial metrics and named scope table of a Composition
    for reuse when embedded as a sub-composition inside another Composition.
    """
    def __init__(
        self,
        root_dimensions: Dimensions,
        envelope_span: Dimensions,
        scopes: Dict[str, ScopeNode]
    ):
        self.root_dimensions = root_dimensions
        self.envelope_span = envelope_span
        self.scopes = scopes


class CompositionCompiler:
    """
    Resolves intrinsic bind(...) and anchor(...) formulas across raw Composition
    dictionaries in topological DAG order prior to Pydantic validation.
    """

    @classmethod
    def compile(
        cls,
        merged_config: Dict[str, Any],
        properties: PropertiesSchema
    ) -> Dict[str, Any]:
        compositions = merged_config.get(Shortcuts.COMPOSITIONS.value)
        if not isinstance(compositions, dict) or properties is None:
            return merged_config

        materials_cfg = merged_config.get("materials", {})
        bp_cfg = (
            materials_cfg.get("blueprints", {})
            if isinstance(materials_cfg, dict)
            else {}
        )

        ordered_ids = cls._topological_sort(compositions)
        compiled_meta: Dict[str, CompiledCompositionMeta] = {}

        for comp_id in ordered_ids:
            comp_data = compositions.get(comp_id)
            if not isinstance(comp_data, dict):
                continue
            compiled_meta[comp_id] = cls._compile_composition(
                comp_id,
                comp_data,
                properties,
                bp_cfg,
                compiled_meta
            )

        return merged_config

    # ---------------------------------------------------------
    # --------------------------------------- DAG & TOPOLOGY
    # ---------------------------------------------------------

    @classmethod
    def _extract_dependencies(cls, comp_data: Dict[str, Any]) -> Set[str]:
        deps: Set[str] = set()
        nodes = [comp_data.get("root")]
        nodes.extend(comp_data.get("branches") or [])

        for node in nodes:
            if not isinstance(node, dict):
                continue
            components = node.get("components")
            if not isinstance(components, dict):
                continue
            sub_comps = components.get(Shortcuts.COMPOSITIONS.value)
            if not isinstance(sub_comps, list):
                continue
            for item in sub_comps:
                if isinstance(item, dict) and item.get("id"):
                    deps.add(str(item["id"]))
        return deps

    @classmethod
    def _topological_sort(cls, compositions: Dict[str, Any]) -> List[str]:
        """
        Orders compositions bottom-up (leaf compositions before composite parents)
        and raises ValueError if a recursive composition cycle exists.
        """
        UNVISITED, VISITING, VISITED = 0, 1, 2
        state: Dict[str, int] = {k: UNVISITED for k in compositions}
        order: List[str] = []

        def _dfs(comp_id: str, path: List[str]) -> None:
            state[comp_id] = VISITING
            comp_data = compositions.get(comp_id)
            if isinstance(comp_data, dict):
                for dep_id in cls._extract_dependencies(comp_data):
                    if dep_id not in compositions:
                        continue
                    if state[dep_id] == VISITING:
                        cycle_chain = " -> ".join([*path, dep_id])
                        raise ValueError(
                            f"Circular Composition dependency detected: {cycle_chain}"
                        )
                    if state[dep_id] == UNVISITED:
                        _dfs(dep_id, [*path, dep_id])
            state[comp_id] = VISITED
            order.append(comp_id)

        for comp_id in compositions:
            if state[comp_id] == UNVISITED:
                _dfs(comp_id, [comp_id])

        return order

    # ---------------------------------------------------------
    # ---------------------------------------- SCOPE & METRICS
    # ---------------------------------------------------------

    @classmethod
    def _get_props(
        cls,
        properties: PropertiesSchema,
        cat_key: str,
        inst_key: str,
        asset_id: Optional[str]
    ) -> Optional[AssetProperties]:
        if not asset_id:
            return None
        prop_inst = (
            AssetInstances.SPRITES.value
            if cat_key == AssetCategories.SHEETS.value
            and inst_key == AssetInstances.PLAYERS.value
            else inst_key
        )
        cat_props = getattr(properties, cat_key, None)
        inst_props = getattr(cat_props, prop_inst, None) if cat_props else None
        return inst_props.get(asset_id) if isinstance(inst_props, dict) else None

    @classmethod
    def _compute_span(
        cls,
        raw_state: Dict[str, Any],
        props: Optional[AssetProperties],
        bp_cfg: Dict[str, Any]
    ) -> Dimensions:
        if not props or not props.dimensions:
            return Dimensions(0, 0)

        w, l = props.dimensions.w, props.dimensions.l
        mul = raw_state.get("multiple")
        nx = int(mul.get("nx", 1)) if isinstance(mul, dict) and isinstance(mul.get("nx"), int) else 1
        ny = int(mul.get("ny", 1)) if isinstance(mul, dict) and isinstance(mul.get("ny"), int) else 1

        bp_schema = getattr(props, "blueprints", None)
        strategy = (
            bp_cfg.get(bp_schema, {}).get("strategy", MultiplicationStrategies.SIMPLE.value)
            if bp_schema and isinstance(bp_cfg.get(bp_schema), dict)
            else MultiplicationStrategies.SIMPLE.value
        )

        if strategy == MultiplicationStrategies.EXPANSION.value:
            return Dimensions(w * nx, l * (ny + 2))
        if strategy == MultiplicationStrategies.PERIMETER.value:
            return Dimensions(w * (nx + 2), l * (ny + 2))
        if strategy == MultiplicationStrategies.ORIENTED.value:
            if raw_state.get("blueprint") == Orientations.HORIZONTAL.value:
                return Dimensions(w * nx, l)
            return Dimensions(w, l * ny)

        return Dimensions(w * nx, l * ny)

    @classmethod
    def _build_node(
        cls,
        raw_state: Dict[str, Any],
        cat_key: str,
        inst_key: str,
        properties: PropertiesSchema,
        bp_cfg: Dict[str, Any],
        parent_node: Optional[ScopeNode] = None,
        root_node: Optional[ScopeNode] = None
    ) -> ScopeNode:
        props = cls._get_props(properties, cat_key, inst_key, raw_state.get("id"))
        span = cls._compute_span(raw_state, props, bp_cfg)
        return ScopeNode(raw_state, props, span, parent_node=parent_node, root_node=root_node)

    @classmethod
    def _build_subcomposition_node(
        cls,
        raw_state: Dict[str, Any],
        compiled_meta: Dict[str, CompiledCompositionMeta],
        parent_node: ScopeNode,
        root_node: ScopeNode
    ) -> ScopeNode:
        sub_id = str(raw_state.get("id", ""))
        meta = compiled_meta.get(sub_id)
        if meta is None:
            return ScopeNode(
                raw_state,
                None,
                Dimensions(0, 0),
                parent_node=parent_node,
                root_node=root_node
            )

        return ScopeNode(
            raw_state,
            None,
            meta.envelope_span,
            parent_node=parent_node,
            root_node=root_node,
            dimensions=meta.root_dimensions,
            children=meta.scopes
        )

    # ---------------------------------------------------------
    # --------------------------------- COMPILATION PIPELINE
    # ---------------------------------------------------------

    @classmethod
    def _compile_composition(
        cls,
        comp_id: str,
        comp_data: Dict[str, Any],
        properties: PropertiesSchema,
        bp_cfg: Dict[str, Any],
        compiled_meta: Dict[str, CompiledCompositionMeta]
    ) -> CompiledCompositionMeta:
        root_data = comp_data.get("root")
        if not isinstance(root_data, dict):
            return CompiledCompositionMeta(Dimensions(0, 0), Dimensions(0, 0), {})

        global_scopes: Dict[str, ScopeNode] = {}
        all_nodes: List[ScopeNode] = []
        root_layer_nodes: List[ScopeNode] = []

        # 1. Index Root Strut
        root_strut_raw = root_data.get("strut") or {}
        root_node = cls._build_node(
            root_strut_raw,
            AssetCategories.CRAFTS.value,
            AssetInstances.STRUTS.value,
            properties,
            bp_cfg
        )
        root_node.parent = root_node
        root_node.root = root_node
        all_nodes.append(root_node)
        root_layer_nodes.append(root_node)
        if root_strut_raw.get("name"):
            global_scopes[root_strut_raw["name"]] = root_node

        # 2. Index Root Components (including nested compositions)
        cls._register_components(
            root_data.get("components"),
            root_node,
            root_node,
            properties,
            bp_cfg,
            compiled_meta,
            global_scopes,
            all_nodes,
            root_layer_nodes=root_layer_nodes
        )

        # 3. Index Branches and Branch Components
        for branch_data in comp_data.get("branches") or []:
            if not isinstance(branch_data, dict):
                continue
            branch_strut_raw = branch_data.get("strut") or {}
            branch_node = cls._build_node(
                branch_strut_raw,
                AssetCategories.CRAFTS.value,
                AssetInstances.STRUTS.value,
                properties,
                bp_cfg,
                parent_node=root_node,
                root_node=root_node
            )
            all_nodes.append(branch_node)
            if branch_strut_raw.get("layer") is None:
                root_layer_nodes.append(branch_node)
            if branch_strut_raw.get("name"):
                global_scopes[branch_strut_raw["name"]] = branch_node

            cls._register_components(
                branch_data.get("components"),
                root_node,
                branch_node,
                properties,
                bp_cfg,
                compiled_meta,
                global_scopes,
                all_nodes,
                root_layer_nodes=root_layer_nodes if branch_strut_raw.get("layer") is None else None
            )

        # 4. Evaluate all bind(...) expressions
        evaluating: Set[Tuple[int, str]] = set()
        for node in all_nodes:
            cls._evaluate_node_dict(node._raw, node, global_scopes, evaluating, include_anchors=False)

        # 5. Evaluate all anchor(...) expressions
        for node in all_nodes:
            cls._evaluate_node_dict(node._raw, node, global_scopes, evaluating, include_anchors=True)

        # 6. Compute root-layer composite bounding envelope
        max_w = root_node.span.w
        max_l = root_node.span.l
        for r_node in root_layer_nodes:
            if r_node._raw.get("layer") is not None:
                continue
            ext_x = r_node.position.x + r_node.span.w
            ext_y = r_node.position.y + r_node.span.l
            if ext_x > max_w:
                max_w = ext_x
            if ext_y > max_l:
                max_l = ext_y

        return CompiledCompositionMeta(
            root_dimensions=root_node.dimensions,
            envelope_span=Dimensions(max_w, max_l),
            scopes=global_scopes
        )

    @classmethod
    def _register_components(
        cls,
        components: Any,
        root_node: ScopeNode,
        parent_node: ScopeNode,
        properties: PropertiesSchema,
        bp_cfg: Dict[str, Any],
        compiled_meta: Dict[str, CompiledCompositionMeta],
        global_scopes: Dict[str, ScopeNode],
        all_nodes: List[ScopeNode],
        root_layer_nodes: Optional[List[ScopeNode]] = None
    ) -> None:
        if not isinstance(components, dict):
            return

        for cat_key, cat_val in components.items():
            # Nested Compositions: components.compositions is a List[Dict]
            if cat_key == Shortcuts.COMPOSITIONS.value and isinstance(cat_val, list):
                for sub_raw in cat_val:
                    if not isinstance(sub_raw, dict):
                        continue
                    sub_node = cls._build_subcomposition_node(
                        sub_raw,
                        compiled_meta,
                        parent_node=parent_node,
                        root_node=root_node
                    )
                    all_nodes.append(sub_node)
                    if root_layer_nodes is not None:
                        root_layer_nodes.append(sub_node)
                    if sub_raw.get("name"):
                        global_scopes[sub_raw["name"]] = sub_node
                continue

            if not isinstance(cat_val, dict):
                continue

            for inst_key, inst_list in cat_val.items():
                if not isinstance(inst_list, list):
                    continue
                for comp_raw in inst_list:
                    if not isinstance(comp_raw, dict):
                        continue
                    comp_node = cls._build_node(
                        comp_raw,
                        cat_key,
                        inst_key,
                        properties,
                        bp_cfg,
                        parent_node=parent_node,
                        root_node=root_node
                    )
                    all_nodes.append(comp_node)
                    if root_layer_nodes is not None:
                        root_layer_nodes.append(comp_node)
                    if comp_raw.get("name"):
                        global_scopes[comp_raw["name"]] = comp_node

    # ---------------------------------------------------------
    # ----------------------------------- EXPRESSION EVALUATION
    # ---------------------------------------------------------

    @classmethod
    def _local_scopes(
        cls,
        self_node: ScopeNode,
        global_scopes: Dict[str, ScopeNode]
    ) -> Dict[str, ScopeNode]:
        scopes = dict(global_scopes)
        scopes["self"] = self_node
        if self_node.parent is not None:
            scopes["parent"] = self_node.parent
        if self_node.root is not None:
            scopes["root"] = self_node.root
        return scopes

    @classmethod
    def _evaluate_node_dict(
        cls,
        data: Dict[str, Any],
        self_node: ScopeNode,
        global_scopes: Dict[str, ScopeNode],
        evaluating: Set[Tuple[int, str]],
        include_anchors: bool,
        prefix: str = ""
    ) -> None:
        for k, v in list(data.items()):
            field_path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                cls._evaluate_node_dict(
                    v,
                    self_node,
                    global_scopes,
                    evaluating,
                    include_anchors=include_anchors,
                    prefix=field_path
                )
            elif isinstance(v, str):
                if not include_anchors and "anchor(" in v:
                    continue
                resolved = cls._evaluate_expression(
                    v,
                    self_node,
                    global_scopes,
                    evaluating,
                    field_path=field_path,
                    include_anchors=include_anchors
                )
                if resolved is not None:
                    data[k] = resolved

    @classmethod
    def _resolve_path(
        cls,
        target_node: ScopeNode,
        attr_path: str,
        global_scopes: Dict[str, ScopeNode],
        evaluating: Set[Tuple[int, str]],
        include_anchors: bool
    ) -> Any:
        parts = attr_path.strip().split(".")
        curr: Any = target_node

        for idx, part in enumerate(parts):
            if isinstance(curr, ScopeNode):
                if part in curr.children:
                    curr = curr.children[part]
                elif part in curr._raw:
                    raw_val = curr._raw[part]
                    sub_path = ".".join(parts[: idx + 1])
                    if isinstance(raw_val, str):
                        resolved = cls._evaluate_expression(
                            raw_val,
                            curr,
                            global_scopes,
                            evaluating,
                            field_path=sub_path,
                            include_anchors=include_anchors
                        )
                        if resolved is not None:
                            curr._raw[part] = resolved
                            curr = resolved
                        else:
                            return None
                    else:
                        curr = raw_val
                elif hasattr(curr, part):
                    curr = getattr(curr, part)
                elif curr.properties and hasattr(curr.properties, part):
                    curr = getattr(curr.properties, part)
                else:
                    return None
            elif isinstance(curr, dict):
                raw_val = curr.get(part)
                sub_path = ".".join(parts[: idx + 1])
                if isinstance(raw_val, str):
                    resolved = cls._evaluate_expression(
                        raw_val,
                        target_node,
                        global_scopes,
                        evaluating,
                        field_path=sub_path,
                        include_anchors=include_anchors
                    )
                    if resolved is not None:
                        curr[part] = resolved
                        curr = resolved
                    else:
                        return None
                else:
                    curr = raw_val
            else:
                curr = getattr(curr, part, None)

            if curr is None:
                return None

        return curr

    @classmethod
    def _evaluate_anchor(
        cls,
        target_key: str,
        self_node: ScopeNode,
        scopes: Dict[str, ScopeNode]
    ) -> int:
        # Support dotted child anchor targets, e.g. anchor(north-cottage.exterior)
        parts = target_key.strip().split(".")
        target_node = scopes.get(parts[0])
        offset_y = 0

        if target_node is not None and len(parts) > 1:
            for sub_part in parts[1:]:
                if target_node is not None and sub_part in target_node.children:
                    if target_node is not self_node.parent and target_node is not self_node.root:
                        offset_y += target_node.position.y
                    target_node = target_node.children[sub_part]
                else:
                    target_node = None
                    break

        if target_node is None:
            logger.warning(
                f"CompositionCompiler: Unresolved anchor target '{target_key}', defaulting to 0."
            )
            return 0

        target_y = (
            0
            if target_node is self_node.parent or target_node is self_node.root
            else offset_y + target_node.position.y
        )
        target_bottom = target_y + target_node.span.l
        self_bottom = self_node.position.y + self_node.span.l
        return int(target_bottom - self_bottom)

    @classmethod
    def _evaluate_expression(
        cls,
        expr_str: str,
        self_node: ScopeNode,
        global_scopes: Dict[str, ScopeNode],
        evaluating: Set[Tuple[int, str]],
        field_path: str = "",
        include_anchors: bool = False
    ) -> Any:
        stripped = expr_str.strip()
        if "bind(" not in stripped and "anchor(" not in stripped:
            return stripped

        state_key = (id(self_node), field_path)
        if field_path and state_key in evaluating:
            raise ValueError(
                f"Circular Composition macro reference detected at '{field_path}': {expr_str}"
            )

        if field_path:
            evaluating.add(state_key)

        try:
            scopes = cls._local_scopes(self_node, global_scopes)

            single_match = SINGLE_BIND_PATTERN.match(stripped)
            if single_match:
                inner = single_match.group(1).strip()
                if not any(op in inner for op in ("+", "-", "*", "/", "%", "(")):
                    target_key, attr_path = inner.split(".", 1) if "." in inner else ("root", inner)
                    target_node = scopes.get(target_key.strip())
                    if target_node is None:
                        return None
                    return cls._resolve_path(
                        target_node,
                        attr_path,
                        global_scopes,
                        evaluating,
                        include_anchors
                    )

            unresolved = False

            def _replace_token(match: re.Match) -> str:
                nonlocal unresolved
                macro_type = match.group(1)
                arg = match.group(2).strip()

                if macro_type == "anchor":
                    if not include_anchors:
                        unresolved = True
                        return match.group(0)
                    return str(cls._evaluate_anchor(arg, self_node, scopes))

                target_key, attr_path = arg.split(".", 1) if "." in arg else ("root", arg)
                target_node = scopes.get(target_key.strip())
                if target_node is None:
                    unresolved = True
                    return match.group(0)

                val = cls._resolve_path(
                    target_node,
                    attr_path,
                    global_scopes,
                    evaluating,
                    include_anchors
                )
                if val is None:
                    unresolved = True
                    return match.group(0)
                return str(val)

            substituted = MACRO_TOKEN_PATTERN.sub(_replace_token, stripped)
            if unresolved:
                return None

            return cls._eval_math_ast(substituted)
        finally:
            if field_path:
                evaluating.discard(state_key)

    @classmethod
    def _eval_math_ast(cls, expr: str) -> Union[int, float, Any]:
        tree = ast.parse(expr.strip(), mode="eval")
        result = cls._eval_ast_node(tree.body)
        if isinstance(result, (int, float)):
            return int(round(result))
        return result

    @classmethod
    def _eval_ast_node(cls, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            left = cls._eval_ast_node(node.left)
            right = cls._eval_ast_node(node.right)
            return _BINARY_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            operand = cls._eval_ast_node(node.operand)
            return _UNARY_OPS[type(node.op)](operand)
        raise ValueError(f"Unsupported syntax in Composition macro expression: {ast.dump(node)}")

```

#### 2. `src/app/services/generators/game/decomposer.py`

In `Decomposer._hydrate_state()` and `Decomposer._unpack_components()`:

1. **Additive Relative Elevation**: In `_hydrate_state()`, relative component elevations add to `parent_context["elevation"]` (`parent_elev + (kwargs.get("elevation") or 0)`), ensuring that a sub-composition placed on an elevated terrace ($E = 1$) elevates all of its constituent struts and components by $+1$.
2. **Recursive `components.compositions` Dispatch**: In `_unpack_components()`, before skipping non-asset `Shortcuts`, check `if cat_key == Shortcuts.COMPOSITIONS.value:`, hydrate each nested `PropertyState`, and pass it recursively to `self.unpack(sub_state)`.

```python
    def _hydrate_state(
        self,
        state_obj: AssetState,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        inst_key: str,
        is_strut: bool = False
    ) -> AssetState:
        """
        Hydrates a validated component, strut, or nested composition PseudoState
        with deployment-time coordinates, layer namespacing, and inherited context.
        """
        layer_map = root_context["_layer_map"]
        link_map = root_context["_link_map"]
        root_layer = root_context["layer"]

        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)

        # 1. Layer, Owner & Additive Elevation Inheritance
        if "layer" in kwargs:
            if kwargs["layer"]:
                kwargs["layer"] = self._resolve_layer(kwargs["layer"], root_layer, inc, layer_map)
            else:
                kwargs["layer"] = parent_context["layer"]

        if "owner" in kwargs and not kwargs["owner"]:
            kwargs["owner"] = parent_context["owner"]

        parent_elev = parent_context.get("elevation") or 0
        local_elev = kwargs.get("elevation")
        kwargs["elevation"] = parent_elev + local_elev if local_elev is not None else parent_elev

        # 2. Door Outlayer Namespacing
        if "outlayer" in kwargs and kwargs["outlayer"]:
            kwargs["outlayer"] = self._resolve_layer(kwargs["outlayer"], root_layer, inc, layer_map)

        # 3. Coordinate Translation
        is_cross_layer = str(kwargs.get("layer")) != str(parent_context.get("layer"))
        base_pos = Position(0, 0) if is_cross_layer else parent_context["position"]

        pseudo_pos = kwargs.get("position")
        if pseudo_pos:
            kwargs["position"] = Position(
                x=base_pos.x + pseudo_pos.x,
                y=base_pos.y + pseudo_pos.y
            )
        else:
            kwargs["position"] = Position(base_pos.x, base_pos.y)

        # 4. Teleport Out Coordinate Translation
        pseudo_out = kwargs.get("out")
        if pseudo_out:
            if str(kwargs.get("outlayer")) == str(root_layer):
                kwargs["out"] = Position(
                    x=root_context["position"].x + pseudo_out.x,
                    y=root_context["position"].y + pseudo_out.y
                )
            else:
                kwargs["out"] = Position(pseudo_out.x, pseudo_out.y)

        # 5. SwitchState Link Namespacing
        if "link" in kwargs and kwargs["link"]:
            link_target = str(kwargs["link"])
            if link_target in link_map:
                kwargs["link"] = link_map[link_target]

        # 6. Unique Entity Nomenclature
        base_inst = inst_key[:-1] if inst_key.endswith("s") else inst_key
        if is_strut:
            b_name = kwargs.get("name") or root_context["name"]
            kwargs["name"] = settings.SEPARATOR.join([base_inst, b_name, str(inc)])
        else:
            comp_name = kwargs.get("name") or "comp"
            kwargs["name"] = settings.SEPARATOR.join([base_inst, parent_context["name"], comp_name, str(inc)])

        return type(state_obj)(**kwargs)

```

And in `Decomposer._unpack_components()`:

```python
    def _unpack_components(
        self,
        components: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        assets: List[Asset]
    ) -> None:
        if not components:
            return

        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name

            # 1. Recursive Sub-Composition Hydration
            if cat_key == Shortcuts.COMPOSITIONS.value:
                sub_compositions = getattr(components, cat_key)
                if not sub_compositions:
                    continue
                for sub_pseudo in sub_compositions:
                    sub_state = self._hydrate_state(
                        sub_pseudo,
                        root_context,
                        parent_context,
                        inc,
                        Shortcuts.COMPOSITIONS.value,
                        is_strut=False
                    )
                    assets.extend(self.unpack(sub_state))
                continue

            if cat_key in Shortcuts:
                continue

            cat_data = getattr(components, cat_key)
            if not cat_data:
                continue

            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list:
                    continue

                for pseudo_state in inst_list:
                    new_state = self._hydrate_state(
                        pseudo_state,
                        root_context,
                        parent_context,
                        inc,
                        inst_key,
                        is_strut=False
                    )

                    if inst_key in MultipliedAssets:
                        assets.extend(self.multiply(new_state, cat_key, inst_key))
                    elif inst_key == AssetInstances.DOORS.value:
                        assets.extend(self.project(new_state))
                    else:
                        assets.append(self._asset(cat_key, inst_key, new_state))

```

##### Example: Composition Within a Composition (`homestead-plot`)

Using the above implementation, a `homestead-plot` Composition can embed two `brick-house` Compositions alongside an enclosure fence (`palisade`) and a courtyard sign (`plaque`), positioning the second house and the sign algebraically via `west-house.span.w` and `west-house.span.l`:

```yaml
compositions:
  homestead-plot:
    root:
      strut:
        id: avenue
        name: courtyard-paving
        material: limestone
        blueprint: solids
        multiple:
          nx: 8
          ny: 8
      components:
        compositions:
          - id: brick-house
            name: west-house
            position:
              x: 16
              y: 16
          - id: brick-house
            name: east-house
            position:
              x: bind(west-house.position.x) + bind(west-house.span.w) + 32
              y: bind(west-house.position.y)
        objects:
          signs:
            - id: plaque
              name: homestead-sign
              material: granite
              anchor: anchor(west-house.exterior)
              persona: narrator
              lexicon: welcome
              position:
                x: bind(west-house.position.x) + bind(west-house.span.w) + 4
                y: bind(west-house.position.y) + bind(west-house.span.l) - bind(self.dimensions.l)

```

When `homestead-plot` is deployed once in a state file at `(200, 200)` on layer `'0'`:

1. `courtyard-paving` unpacks at `(200, 200)` with $\text{inc} = 1$.
2. `west-house` unpacks at `(216, 216)` with $\text{inc} = 2$ and isolated interior layer `house-layer-2` (whose exit Door returns to layer `'0'` at `west-house`'s threshold).
3. `east-house` unpacks at `(344, 216)` with $\text{inc} = 3$ and isolated interior layer `house-layer-3` (whose exit Door returns to layer `'0'` at `east-house`'s threshold).
4. `homestead-sign` unpacks at `(316, 384)` aligned to the baseline of `west-house.exterior`.