"""
@domain.logic
@workflow.compositions

# Ontology: Source - app.static.macros.compositions

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
    Compile-time proxy for a Composition entity exposing its static
    AssetProperties, multiplied span Dimensions, and raw PseudoState dictionary.
    """
    def __init__(
        self,
        raw_state: Dict[str, Any],
        props: Optional[AssetProperties],
        span: Dimensions,
        parent_node: Optional["ScopeNode"] = None,
        root_node: Optional["ScopeNode"] = None
    ):
        self._raw = raw_state
        self.properties = props
        self.dimensions = (
            props.dimensions
            if props and props.dimensions
            else Dimensions(0, 0)
        )
        self.span = span
        self.parent = parent_node
        self.root = root_node

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


class CompositionCompiler:
    """
    Resolves intrinsic bind(...) and anchor(...) formulas (including self
    references and algebraic expressions) across raw Composition dictionaries
    prior to Pydantic StateSchema validation.
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

        for comp_id, comp_data in compositions.items():
            if not isinstance(comp_data, dict):
                continue
            cls._compile_composition(comp_id, comp_data, properties, bp_cfg)

        return merged_config

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

    # ---------------------------------------------------------
    # --------------------------------- COMPILATION PIPELINE
    # ---------------------------------------------------------

    @classmethod
    def _compile_composition(
        cls,
        comp_id: str,
        comp_data: Dict[str, Any],
        properties: PropertiesSchema,
        bp_cfg: Dict[str, Any]
    ) -> None:
        root_data = comp_data.get("root")
        if not isinstance(root_data, dict):
            return

        global_scopes: Dict[str, ScopeNode] = {}
        all_nodes: list[ScopeNode] = []

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
        if root_strut_raw.get("name"):
            global_scopes[root_strut_raw["name"]] = root_node

        # 2. Index Root Components
        cls._register_components(
            root_data.get("components"),
            root_node,
            root_node,
            properties,
            bp_cfg,
            global_scopes,
            all_nodes
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
            if branch_strut_raw.get("name"):
                global_scopes[branch_strut_raw["name"]] = branch_node

            cls._register_components(
                branch_data.get("components"),
                root_node,
                branch_node,
                properties,
                bp_cfg,
                global_scopes,
                all_nodes
            )

        # 4. Evaluate all bind(...) expressions (with demand-driven dependency resolution)
        evaluating: Set[Tuple[int, str]] = set()
        for node in all_nodes:
            cls._evaluate_node_dict(node._raw, node, global_scopes, evaluating, include_anchors=False)

        # 5. Evaluate all anchor(...) expressions now that positions and spans are concrete
        for node in all_nodes:
            cls._evaluate_node_dict(node._raw, node, global_scopes, evaluating, include_anchors=True)

    @classmethod
    def _register_components(
        cls,
        components: Any,
        root_node: ScopeNode,
        parent_node: ScopeNode,
        properties: PropertiesSchema,
        bp_cfg: Dict[str, Any],
        global_scopes: Dict[str, ScopeNode],
        all_nodes: list[ScopeNode]
    ) -> None:
        if not isinstance(components, dict):
            return

        for cat_key, cat_dict in components.items():
            if not isinstance(cat_dict, dict):
                continue
            for inst_key, inst_list in cat_dict.items():
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
        """
        Resolves a dotted path (e.g. 'dimensions.l', 'position.y', 'material')
        on target_node, evaluating raw macro strings on demand if encountered.
        """
        parts = attr_path.strip().split(".")
        curr: Any = target_node

        for idx, part in enumerate(parts):
            if isinstance(curr, ScopeNode):
                # 1. Check raw state dictionary first for dynamic/overridden fields
                if part in curr._raw:
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
        target_node = scopes.get(target_key.strip())
        if target_node is None:
            logger.warning(
                f"CompositionCompiler: Unresolved anchor target '{target_key}', defaulting to 0."
            )
            return 0

        # When anchoring to the immediate parent or root strut, the parent's local origin is y = 0
        target_y = (
            0
            if target_node is self_node.parent or target_node is self_node.root
            else target_node.position.y
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

            # Fast path: single standalone bind(target.path) without outer arithmetic
            single_match = SINGLE_BIND_PATTERN.match(stripped)
            if single_match:
                inner = single_match.group(1).strip()
                # If inner expression contains no arithmetic operators, resolve directly to preserve type
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

            # General path: substitute all bind(...) and anchor(...) tokens and evaluate AST
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
        """
        Safely evaluates an arithmetic string via Python's AST without eval().
        """
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