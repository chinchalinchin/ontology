"""
@domain.test
@domain.system
@test.unit
@app.config
@app.schema
@app.asset
@asset.state
@asset.property
@workflow.hydration

# Ontology: Tests - tests.unit.app.static.test_loader

Unit tests verifying YAML dictionary merging, Cython struct adapters,
Enumerated primitive extraction, full PropertiesSchema/ConfigurationSchema/StateSchema
hydration, referential integrity, and StateSchema round-trip serialization.
"""
# Standard Libraries
from dataclasses import fields
from enum import Enum
import warnings

# External Libraries
import pytest
from pydantic import TypeAdapter, ValidationError

# Application Libraries
from app.models.adapters import (
    Enumerated,
    PydanticDimensions,
    PydanticHitbox,
    PydanticMultiple,
    PydanticPosition,
    PydanticScreenPosition,
    PydanticVelocity,
)
from app.models.config import (
    ActionConfiguration,
    CompositionConfiguration,
    ConfigurationSchema,
    DeviceMapping,
    IntentionConfiguration,
    MappingConfiguration,
    MaterialsConfiguration,
    MechanicsConfiguration,
    MechanicsInstance,
    MenuConfiguration,
    PlotConfiguration,
    Recipe,
    RecipeConfiguration,
    StageConfiguration,
)
from app.models.properties import (
    Action,
    CraftProperties,
    CursorProperties,
    Direction,
    EffectProperties,
    FontProperties,
    Frequency,
    GeographyProperties,
    Material,
    ObjectProperties,
    Outline,
    PropertiesSchema,
    ResourceProperties,
    RGBA,
    SheetProperties,
    TileProperties,
    WidgetProperties,
)
from app.models.state import (
    AnimationState,
    CalendarState,
    Character,
    CollectableState,
    ContainerState,
    CraftState,
    DialogueState,
    DoorState,
    EffectState,
    Equipment,
    FluidState,
    Goal,
    HazardState,
    Inventory,
    Memory,
    Meters,
    MotiveState,
    MultiplierState,
    Mutators,
    PlotState,
    PropertyState,
    Psyche,
    ReactableState,
    ResourceState,
    SheetState,
    SpriteState,
    StairState,
    StateSchema,
    SwitchState,
    Trajectory,
)
from app.static.loader import Loader
from app.static.semantics import (
    Actions,
    AnnualStages,
    AssetCategories,
    AssetInstances,
    Ceramics,
    Cycles,
    Directions,
    ExpressionsPalette,
    Fonts,
    Frequencies,
    Geologics,
    Intentions,
    Lifespans,
    Materials,
    Metallics,
    Organics,
    PerennialStages,
    Relationships,
    Seasons,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Multiple,
    Position,
    ScreenPosition,
    Velocity,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_config,
    pytest.mark.workflow_hydration,
]

# ---------------------------------------------------------------------------
# ------------------------------------------------------------- LOADER MERGE
# ---------------------------------------------------------------------------


@pytest.mark.app_schema
def test_loader_merge_recursive_dictionaries():
    """
    Verifies Loader.merge() recursively merges nested dictionaries without
    overwriting sibling keys under shared top-level namespaces.
    """
    base = {
        "objects": {
            "chests": [{"id": "trunk"}],
        },
        "plots": {"current": "initial"},
    }
    incoming = {
        "objects": {
            "crates": [{"id": "box"}],
        },
        "plots": {"current": "updated"},
    }

    merged = Loader.merge(base, incoming)

    assert "chests" in merged["objects"]
    assert "crates" in merged["objects"]
    assert merged["objects"]["chests"][0]["id"] == "trunk"
    assert merged["objects"]["crates"][0]["id"] == "box"
    assert merged["plots"]["current"] == "updated"


# ---------------------------------------------------------------------------
# ------------------------------------------------- CYTHON & ENUMERATED TYPES
# ---------------------------------------------------------------------------


@pytest.mark.app_schema
def test_cython_adapters_validation_and_serialization():
    """
    Verifies bidirectional Pydantic validation and JSON-mode serialization
    for all Cython extension types in libs.core.models.
    """
    pos_adapter = TypeAdapter(PydanticPosition)
    dim_adapter = TypeAdapter(PydanticDimensions)
    mul_adapter = TypeAdapter(PydanticMultiple)
    vel_adapter = TypeAdapter(PydanticVelocity)
    hb_adapter = TypeAdapter(PydanticHitbox)
    sp_adapter = TypeAdapter(PydanticScreenPosition)

    # 1. Deserialize dicts into Cython extension structs
    pos = pos_adapter.validate_python({"x": 16, "y": 32})
    dim = dim_adapter.validate_python({"w": 64, "l": 48})
    mul = mul_adapter.validate_python({"nx": 4, "ny": 8})
    vel = vel_adapter.validate_python({"vx": 2.5, "vy": -1.5})
    hb = hb_adapter.validate_python(
        {"position": {"x": 8, "y": 12}, "dimensions": {"w": 16, "l": 20}}
    )
    sp = sp_adapter.validate_python({"px": 0.25, "py": 0.75})

    assert isinstance(pos, Position) and (pos.x, pos.y) == (16, 32)
    assert isinstance(dim, Dimensions) and (dim.w, dim.l) == (64, 48)
    assert isinstance(mul, Multiple) and (mul.nx, mul.ny) == (4, 8)
    assert isinstance(vel, Velocity) and (vel.vx, vel.vy) == (2.5, -1.5)
    assert isinstance(hb, Hitbox)
    assert isinstance(hb.position, Position) and (hb.position.x, hb.position.y) == (8, 12)
    assert isinstance(hb.dimensions, Dimensions) and (hb.dimensions.w, hb.dimensions.l) == (16, 20)
    assert isinstance(sp, ScreenPosition) and (sp.px, sp.py) == (0.25, 0.75)

    # 2. Passthrough validation when given existing Cython instances
    assert pos_adapter.validate_python(pos) is pos
    assert dim_adapter.validate_python(dim) is dim
    assert mul_adapter.validate_python(mul) is mul
    assert vel_adapter.validate_python(vel) is vel
    assert hb_adapter.validate_python(hb) is hb
    assert sp_adapter.validate_python(sp) is sp

    # 3. Serialize back to primitive dicts
    assert pos_adapter.dump_python(pos, mode="json") == {"x": 16, "y": 32}
    assert dim_adapter.dump_python(dim, mode="json") == {"w": 64, "l": 48}
    assert mul_adapter.dump_python(mul, mode="json") == {"nx": 4, "ny": 8}
    assert vel_adapter.dump_python(vel, mode="json") == {"vx": 2.5, "vy": -1.5}
    assert hb_adapter.dump_python(hb, mode="json") == {
        "position": {"x": 8, "y": 12},
        "dimensions": {"w": 16, "l": 20},
    }
    assert sp_adapter.dump_python(sp, mode="json") == {"px": 0.25, "py": 0.75}


def test_enumerated_adapter_extracts_primitive_and_validates():
    """
    Verifies Enumerated validates against the target Enum, strips the Enum
    wrapper to store a raw str primitive, serializes without warnings, and
    rejects invalid values.
    """
    season_adapter = TypeAdapter(Enumerated[Seasons])

    from_str = season_adapter.validate_python("autumn")
    from_enum = season_adapter.validate_python(Seasons.WINTER)

    assert from_str == "autumn"
    assert type(from_str) is str and not isinstance(from_str, Enum)
    assert from_enum == "winter"
    assert type(from_enum) is str and not isinstance(from_enum, Enum)

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        assert season_adapter.dump_python(from_str, mode="json") == "autumn"

    with pytest.raises(ValidationError):
        season_adapter.validate_python("monsoon")


@pytest.mark.modality_material
def test_material_chromatic_host_validation():
    """
    Verifies Material enforces chromatic host requirements and rejects
    host declarations on non-chromatic genera.
    """
    material_adapter = TypeAdapter(Material)

    chromatic_organic = material_adapter.validate_python(
        {"genus": "chromatics", "host": "cotton"}
    )
    assert chromatic_organic.genus == Materials.CHROMATICS.value
    assert chromatic_organic.host == Organics.COTTON.value
    assert type(chromatic_organic.genus) is str
    assert type(chromatic_organic.host) is str

    chromatic_ceramic = material_adapter.validate_python(
        {"genus": "chromatics", "host": "clay"}
    )
    assert chromatic_ceramic.host == Ceramics.CLAY.value

    geologic = material_adapter.validate_python({"genus": "geologics"})
    assert geologic.genus == Materials.GEOLOGICS.value
    assert geologic.host is None

    with pytest.raises(ValidationError):
        material_adapter.validate_python({"genus": "chromatics", "host": None})

    with pytest.raises(ValidationError):
        material_adapter.validate_python({"genus": "geologics", "host": "cotton"})


# ---------------------------------------------------------------------------
# -------------------------------------------------------- PROPERTIES SCHEMA
# ---------------------------------------------------------------------------


@pytest.mark.asset_property
@pytest.mark.app_schema
def test_load_properties_hydrates_entire_schema(
    mock_properties_schema: PropertiesSchema,
):
    """
    Verifies Loader.load_properties() hydrates all asset categories and fonts
    into their respective AssetProperties dataclasses with Cython primitives
    and unpacked Enumerated strings.
    """
    assert isinstance(mock_properties_schema, PropertiesSchema)

    # 1. Tiles
    temperate = mock_properties_schema.tiles.environ["temperate"]
    assert isinstance(temperate, TileProperties)
    assert isinstance(temperate.dimensions, Dimensions)
    assert (temperate.dimensions.w, temperate.dimensions.l) == (32, 32)
    assert isinstance(temperate.friction, float)

    # 2. Crafts
    arch = mock_properties_schema.crafts.bridges["arch"]
    steps = mock_properties_schema.crafts.stairs["steps"]
    crenellation = mock_properties_schema.crafts.struts["crenellation"]
    assert isinstance(arch, CraftProperties)
    assert isinstance(steps, CraftProperties)
    assert isinstance(crenellation, CraftProperties)
    if crenellation.material is not None:
        assert isinstance(crenellation.material, Material)
        assert type(crenellation.material.genus) is str
    if crenellation.blueprints is not None:
        assert type(crenellation.blueprints) is str

    # 3. Cursors
    bubbles = mock_properties_schema.cursors.expressions[
        ExpressionsPalette.BUBBLES.value
    ]
    assert isinstance(bubbles, CursorProperties)
    assert len(bubbles.frames) > 0

    # 4. Effects
    waterflow = mock_properties_schema.effects.fluids["waterflow"]
    torch = mock_properties_schema.effects.passive["torch"]
    dummy = mock_properties_schema.effects.reactables["spinning-dummy"]
    assert isinstance(waterflow, EffectProperties)
    assert isinstance(torch, EffectProperties)
    assert isinstance(dummy, EffectProperties)
    assert isinstance(torch.frequency, Frequency)
    assert type(torch.frequency.type) is str
    assert torch.frequency.type in {f.value for f in Frequencies}

    # 5. Geography
    assert len(mock_properties_schema.geography.shorelines) > 0
    for shore in mock_properties_schema.geography.shorelines.values():
        assert isinstance(shore, GeographyProperties)
        assert isinstance(shore.dimensions, Dimensions)

    # 6. Objects
    trunk = mock_properties_schema.objects.chests["trunk"]
    box = mock_properties_schema.objects.crates["box"]
    postern = mock_properties_schema.objects.gates["postern"]
    rock = mock_properties_schema.objects.obstacles["gray-rock-00"]
    plaque = mock_properties_schema.objects.signs["plaque"]
    rowboat = mock_properties_schema.objects.rafts["rowboat"]
    for obj_prop in (trunk, box, postern, rock, plaque, rowboat):
        assert isinstance(obj_prop, ObjectProperties)
        assert isinstance(obj_prop.dimensions, Dimensions)

    # 7. Resources
    maize = mock_properties_schema.resources.crops["maize"]
    deciduous = mock_properties_schema.resources.trees["deciduous"]
    assert isinstance(maize, ResourceProperties)
    assert isinstance(deciduous, ResourceProperties)
    assert type(maize.lifespan) is str
    assert maize.lifespan == Lifespans.ANNUAL.value
    assert deciduous.lifespan == Lifespans.PERENNIAL.value
    assert isinstance(maize.hitboxes, dict)

    # 8. Sheets & Equipment
    player = mock_properties_schema.sheets.sprites["player"]
    rat = mock_properties_schema.sheets.pixies["giant-rat"]
    shortsword = mock_properties_schema.sheets.weapons["shortsword"]
    buckler = mock_properties_schema.sheets.shields["buckler"]
    for sheet_prop in (player, rat, shortsword, buckler):
        assert isinstance(sheet_prop, SheetProperties)
        assert isinstance(sheet_prop.dimensions, Dimensions)

    assert player.hitboxes is not None and len(player.hitboxes) > 0
    assert isinstance(player.hitboxes[0], Hitbox)
    assert isinstance(player.hitboxes[0].position, Position)
    assert isinstance(player.hitboxes[0].dimensions, Dimensions)
    assert isinstance(player.actions, dict)
    walk_action = player.actions[Actions.WALK.value]
    assert isinstance(walk_action, Action)
    assert isinstance(walk_action.directions[Directions.DOWN.value], Direction)

    # 9. Widgets
    for field_info in fields(mock_properties_schema.widgets):
        bucket = getattr(mock_properties_schema.widgets, field_info.name)
        for widget_prop in bucket.values():
            assert isinstance(widget_prop, WidgetProperties)
            assert isinstance(widget_prop.dimensions, Dimensions)

    # 10. Fonts
    for required_font in (Fonts.DIALOGUE.value, Fonts.MENU.value, Fonts.TITLE.value):
        assert required_font in mock_properties_schema.fonts
        font_prop = mock_properties_schema.fonts[required_font]
        assert isinstance(font_prop, FontProperties)
        assert isinstance(font_prop.color, RGBA)
        if font_prop.outline is not None:
            assert isinstance(font_prop.outline, Outline)
            assert isinstance(font_prop.outline.color, RGBA)


# ---------------------------------------------------------------------------
# ----------------------------------------------------- CONFIGURATION SCHEMA
# ---------------------------------------------------------------------------


@pytest.mark.app_schema
def test_load_configurations_hydrates_entire_schema(
    mock_configurations_schema: ConfigurationSchema,
):
    """
    Verifies Loader.load_configurations() compiles compositions and hydrates
    all configuration subsystems into ConfigurationSchema models.
    """
    assert isinstance(mock_configurations_schema, ConfigurationSchema)

    # 1. Actions
    assert len(mock_configurations_schema.actions) > 0
    for action_cfg in mock_configurations_schema.actions:
        assert isinstance(action_cfg, ActionConfiguration)
        for action_key, action in action_cfg.data.items():
            assert type(action_key) is str
            assert isinstance(action, Action)

    # 2. Compositions (compiled via CompositionCompiler)
    assert "brick-house" in mock_configurations_schema.compositions
    brick_house = mock_configurations_schema.compositions["brick-house"]
    assert isinstance(brick_house, CompositionConfiguration)
    assert isinstance(brick_house.root.strut, PropertyState)
    assert isinstance(brick_house.root.components, StateSchema)

    # 3. Intentions, Plots, and Stages
    assert len(mock_configurations_schema.intentions) > 0
    for transitions in mock_configurations_schema.intentions.values():
        for rule in transitions:
            assert isinstance(rule, IntentionConfiguration)

    assert len(mock_configurations_schema.plots) > 0
    for plot_rules in mock_configurations_schema.plots.values():
        for rule in plot_rules:
            assert isinstance(rule, PlotConfiguration)

    for lifespan_stages in mock_configurations_schema.stages.values():
        for stage_rules in lifespan_stages.values():
            for rule in stage_rules:
                assert isinstance(rule, StageConfiguration)

    # 4. Library
    assert len(mock_configurations_schema.library) > 0

    # 5. Mappings
    assert isinstance(mock_configurations_schema.mappings, MappingConfiguration)
    assert isinstance(mock_configurations_schema.mappings.keyboard, DeviceMapping)
    for menu_key in mock_configurations_schema.mappings.keyboard.world.menus:
        assert type(menu_key) is str
    for intention_key in mock_configurations_schema.mappings.keyboard.world.intentions:
        assert type(intention_key) is str

    # 6. Materials
    materials_cfg = mock_configurations_schema.materials
    assert isinstance(materials_cfg, MaterialsConfiguration)
    assert len(materials_cfg.genera) > 0
    assert len(materials_cfg.blueprints) > 0
    for genus_key, space in materials_cfg.genera.items():
        assert type(genus_key) is str
        for part_key in space.partitions:
            assert type(part_key) is str

    # 7. Mechanics
    mechanics_cfg = mock_configurations_schema.mechanics
    assert isinstance(mechanics_cfg, MechanicsConfiguration)
    assert len(mechanics_cfg.core) > 0
    assert len(mechanics_cfg.world) > 0
    for mech in (*mechanics_cfg.core, *mechanics_cfg.world):
        assert isinstance(mech, MechanicsInstance)
        for ex in mech.executors:
            assert type(ex) is str
        for rel in mech.relations:
            assert type(rel) is str

    # 8. Recipes
    recipes_cfg = mock_configurations_schema.recipes
    assert isinstance(recipes_cfg, RecipeConfiguration)
    assert isinstance(recipes_cfg.tiles.environ, Recipe)
    assert recipes_cfg.tiles.environ.frame == "seasonal"
    assert recipes_cfg.crafts.struts.frame == "material"

    # 9. Menus
    assert len(mock_configurations_schema.menus) > 0
    for menu_cfg in mock_configurations_schema.menus.values():
        assert isinstance(menu_cfg, MenuConfiguration)
        assert len(menu_cfg.roots) > 0


# ---------------------------------------------------------------------------
# ------------------------------------------------------------- STATE SCHEMA
# ---------------------------------------------------------------------------


@pytest.mark.asset_state
@pytest.mark.app_schema
def test_load_state_hydrates_models_and_referential_integrity(
    mock_state_schema: StateSchema,
    mock_properties_schema: PropertiesSchema,
):
    """
    Verifies Loader.load_state() hydrates all entity states, compositions,
    PlotState, and CalendarState with Cython structs, unpacked Enumerated
    strings, and referential integrity against PropertiesSchema.
    """
    assert isinstance(mock_state_schema, StateSchema)

    # 1. Board-level PlotState & CalendarState
    assert isinstance(mock_state_schema.plots, PlotState)
    assert mock_state_schema.plots.current == "castle-dawn-locked"
    assert isinstance(mock_state_schema.calendar, CalendarState)
    assert mock_state_schema.calendar.season == Seasons.SPRING.value
    assert mock_state_schema.calendar.cycle == Cycles.ONSET.value
    assert type(mock_state_schema.calendar.season) is str
    assert type(mock_state_schema.calendar.cycle) is str

    # 2. Virtualized Compositions
    assert len(mock_state_schema.compositions) == 1
    comp = mock_state_schema.compositions[0]
    assert isinstance(comp, PropertyState)
    assert comp.id == "brick-house"
    assert comp.owner == "player"
    assert isinstance(comp.position, Position)

    # 3. Specific State Subclasses & Enumerated Attributes
    stair = mock_state_schema.crafts.stairs[0]
    assert isinstance(stair, StairState)
    assert stair.material == Geologics.GRANITE.value and type(stair.material) is str
    assert type(stair.blueprint) is str

    bridge = mock_state_schema.crafts.bridges[0]
    assert isinstance(bridge, CraftState)
    assert isinstance(bridge.multiple, Multiple)

    chest = mock_state_schema.objects.chests[0]
    assert isinstance(chest, ContainerState)
    assert chest.material == Metallics.GOLD.value
    assert chest.content == ["writ-of-dawn"]

    crate = mock_state_schema.objects.crates[0]
    assert isinstance(crate, MotiveState)
    assert isinstance(crate.velocity, Velocity)

    gate = mock_state_schema.objects.gates[0]
    assert isinstance(gate, SwitchState)
    assert gate.switch is True
    assert gate.link == "test-plate"

    sign = mock_state_schema.objects.signs[0]
    assert isinstance(sign, DialogueState)
    assert sign.persona == "castle-dawn-sign"

    crop = mock_state_schema.resources.crops[0]
    tree = mock_state_schema.resources.trees[0]
    assert isinstance(crop, ResourceState)
    assert isinstance(tree, ResourceState)
    assert crop.stage == AnnualStages.SPROUT.value and type(crop.stage) is str
    assert tree.stage == PerennialStages.SAPLING.value and type(tree.stage) is str

    fluid = mock_state_schema.effects.fluids[0]
    passive = mock_state_schema.effects.passive[0]
    reactable = mock_state_schema.effects.reactables[0]
    assert isinstance(fluid, FluidState)
    assert fluid.source == Directions.DOWN.value and type(fluid.source) is str
    assert isinstance(passive, EffectState)
    assert isinstance(reactable, ReactableState)
    assert reactable.intention == Intentions.ATTACK.value and type(reactable.intention) is str

    player = mock_state_schema.sheets.players[0]
    sprite = mock_state_schema.sheets.sprites[0]
    pixie = mock_state_schema.sheets.pixies[0]
    assert isinstance(player, SheetState)
    assert isinstance(sprite, SpriteState)
    assert isinstance(pixie, SheetState)
    assert isinstance(sprite.character, Character)
    assert isinstance(sprite.meters, Meters)
    assert isinstance(sprite.inventory, Inventory)
    assert isinstance(sprite.inventory.equipment, Equipment)
    assert isinstance(sprite.psyche, Psyche)
    assert isinstance(sprite.goal, Goal)
    assert isinstance(sprite.memory, Memory)
    assert isinstance(sprite.trajectory, Trajectory)
    assert isinstance(sprite.mutators, Mutators)
    assert isinstance(sprite.animation, AnimationState)
    assert sprite.intention == Intentions.FIND.value and type(sprite.intention) is str
    assert sprite.memory.relationships["player"] == Relationships.FRIEND.value
    assert type(sprite.memory.relationships["player"]) is str

    tile = mock_state_schema.tiles.environ[0]
    assert isinstance(tile, MultiplierState)
    assert isinstance(tile.multiple, Multiple)

    # 4. Referential Integrity against PropertiesSchema
    for category in (
        AssetCategories.TILES.value,
        AssetCategories.CRAFTS.value,
        AssetCategories.CURSORS.value,
        AssetCategories.EFFECTS.value,
        AssetCategories.OBJECTS.value,
        AssetCategories.RESOURCES.value,
        AssetCategories.SHEETS.value,
    ):
        state_cat = getattr(mock_state_schema, category)
        prop_cat = getattr(mock_properties_schema, category)

        for instance_field in fields(state_cat):
            instance = instance_field.name
            prop_map = (
                getattr(prop_cat, AssetInstances.SPRITES.value)
                if instance == AssetInstances.PLAYERS.value
                else getattr(prop_cat, instance)
            )

            for entity_state in getattr(state_cat, instance):
                assert entity_state.id in prop_map, (
                    f"State {category}.{instance} references unknown property id '{entity_state.id}'"
                )
                if getattr(entity_state, "position", None) is not None:
                    assert isinstance(entity_state.position, Position)


@pytest.mark.asset_state
@pytest.mark.app_schema
def test_save_and_reload_state_roundtrip(
    mock_state_schema: StateSchema,
    monkeypatch,
    tmp_path,
):
    """
    Verifies Loader.save_state() serializes Cython structs and Enumerated
    primitives without warnings and reloads into an equivalent StateSchema.
    """
    save_root = tmp_path / "save"
    monkeypatch.setattr("app.static.settings.SAVE_DIR", save_root)

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        Loader.save_state("world-testbed", "0", mock_state_schema)

    assert (save_root / "world-testbed" / "slot-0.yaml").is_file()

    reloaded = Loader.load_save("world-testbed", "0")

    assert isinstance(reloaded, StateSchema)
    assert reloaded.plots.current == mock_state_schema.plots.current
    assert reloaded.calendar.season == mock_state_schema.calendar.season
    assert reloaded.calendar.cycle == mock_state_schema.calendar.cycle
    assert len(reloaded.compositions) == len(mock_state_schema.compositions)
    assert len(reloaded.crafts.bridges) == len(mock_state_schema.crafts.bridges)
    assert len(reloaded.objects.chests) == len(mock_state_schema.objects.chests)
    assert len(reloaded.resources.crops) == len(mock_state_schema.resources.crops)
    assert len(reloaded.sheets.players) == len(mock_state_schema.sheets.players)
    assert len(reloaded.sheets.sprites) == len(mock_state_schema.sheets.sprites)
    assert (
        reloaded.sheets.players[0].position.x
        == mock_state_schema.sheets.players[0].position.x
    )
    assert (
        reloaded.sheets.players[0].position.y
        == mock_state_schema.sheets.players[0].position.y
    )