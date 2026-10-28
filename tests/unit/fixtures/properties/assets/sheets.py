"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.sheets

# Ontology: Tests - tests.unit.fixtures.properties.sheets

Mock Sheet Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Actions,
    Directions,
)
from app.models.properties import (
    Action,
    Direction,
    SheetProperties,
    SheetPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox,
)


def _four_dir(start_row: int) -> dict[str, Direction]:
    return {
        Directions.UP.value: Direction(row=start_row),
        Directions.LEFT.value: Direction(row=start_row + 1),
        Directions.DOWN.value: Direction(row=start_row + 2),
        Directions.RIGHT.value: Direction(row=start_row + 3),
    }


def _actions_extended_walk() -> dict[str, Action]:
    return {
        Actions.WALK.value: Action(count=11, directions=_four_dir(0)),
    }


def _actions_lpc_thrust() -> dict[str, Action]:
    return {
        Actions.THRUST.value: Action(count=8, directions=_four_dir(4)),
    }


def _actions_lpc_slash(delay: int = 3) -> dict[str, Action]:
    return {
        Actions.SLASH.value: Action(
            count=6,
            delay=delay,
            directions=_four_dir(12),
        ),
    }


def _actions_lpc_shoot() -> dict[str, Action]:
    return {
        Actions.SHOOT.value: Action(count=13, directions=_four_dir(16)),
    }


def _actions_lpc_full() -> dict[str, Action]:
    return {
        Actions.CAST.value: Action(count=7, directions=_four_dir(0)),
        Actions.THRUST.value: Action(count=8, directions=_four_dir(4)),
        Actions.WALK.value: Action(count=9, delay=3, directions=_four_dir(8)),
        Actions.SLASH.value: Action(count=6, delay=5, directions=_four_dir(12)),
        Actions.SHOOT.value: Action(count=13, directions=_four_dir(16)),
        Actions.DIE.value: Action(
            count=6,
            directions={Directions.UP.value: Direction(row=20)},
        ),
    }


@pytest.fixture
def mock_sheet_properties() -> SheetPropertyInstances:
    lpc_hitbox = Hitbox(Position(23, 34), Dimensions(18, 15))
    lpc_dim = Dimensions(w=64, l=64)

    player_props = SheetProperties(
        mass=7,
        dimensions=lpc_dim,
        attackboxes=None,
        hitboxes=[lpc_hitbox],
        stack=[
            "human-male-ivory",
            "feet-boots-black",
            "legs-robe-black",
            "torso-shirt-male-black",
            "toros-cape-black",
            "head-glasses",
            "head-beard-white",
            "hair-curls-white",
            "head-wizard-hat-moon",
        ],
        actions=_actions_lpc_full(),
    )

    return SheetPropertyInstances(
        players={
            "player": player_props,
        },
        sprites={
            "player": player_props,
            "jasilynn": SheetProperties(
                mass=25,
                dimensions=lpc_dim,
                attackboxes=None,
                hitboxes=[lpc_hitbox],
                stack=[
                    "human-female-ivory",
                    "torso-dress-red",
                    "hair-long-black",
                    "head-crown-gold",
                    "feet-boots-black",
                ],
                actions=_actions_lpc_full(),
            ),
            "archaxes": SheetProperties(
                mass=50,
                dimensions=lpc_dim,
                hitboxes=[lpc_hitbox],
                stack=["human-male-ivory"],
                actions=_actions_lpc_full(),
            ),
        },
        pixies={
            "giant-rat": SheetProperties(
                mass=10,
                dimensions=Dimensions(w=80, l=64),
                attackboxes=None,
                hitboxes=None,
                actions=_actions_extended_walk(),
            ),
        },
        armor={
            "leather": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_full(),
                hitboxes=None,
                stack=[
                    "leather-gloves",
                    "leather-kilt",
                    "leather-sandals",
                ],
            ),
            "plate": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_full(),
                hitboxes=None,
                stack=[
                    "plate-boots",
                    "plate-chest",
                    "plate-gloves",
                    "plate-greaves",
                    "plate-helmet",
                    "plate-shoulders",
                ],
            ),
        },
        shields={
            "buckler": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_full(),
                hitboxes=None,
                stack=["buckler"],
            ),
        },
        utilities={
            "lantern": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_full(),
                hitboxes=None,
                stack=["lantern"],
            ),
        },
        tools={
            "axe": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_slash(),
                hitboxes=None,
                attackboxes=None,
                stack=["axe"],
            ),
            "shovel": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_thrust(),
                attackboxes=None,
                hitboxes=None,
                stack=["shovel"],
            ),
            "pickaxe": SheetProperties(
                dimensions=lpc_dim,
                actions=_actions_lpc_thrust(),
                attackboxes=None,
                hitboxes=None,
                stack=["pickaxe"],
            ),
        },
        weapons={
            "longbow": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes=None,
                actions=_actions_lpc_shoot(),
                stack=["longbow"],
            ),
            "dagger": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes=None,
                actions=_actions_lpc_slash(),
                stack=["dagger"],
            ),
            "knife": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes=None,
                actions=_actions_lpc_slash(),
                stack=["longsword"],
            ),
            "shortsword": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes={
                    "slash-up-3": [Hitbox(Position(5, 39), Dimensions(13, 4))],
                    "slash-up-4": [Hitbox(Position(34, 14), Dimensions(20, 20))],
                    "slash-up-5": [Hitbox(Position(50, 16), Dimensions(7, 24))],
                    "slash-left-3": [Hitbox(Position(11, 44), Dimensions(8, 20))],
                    "slash-left-4": [Hitbox(Position(0, 31), Dimensions(14, 14))],
                    "slash-left-5": [Hitbox(Position(0, 18), Dimensions(16, 17))],
                    "slash-down-3": [Hitbox(Position(15, 45), Dimensions(24, 6))],
                    "slash-down-4": [Hitbox(Position(37, 44), Dimensions(16, 17))],
                    "slash-down-5": [Hitbox(Position(51, 42), Dimensions(9, 20))],
                    "slash-right-3": [Hitbox(Position(46, 44), Dimensions(7, 20))],
                    "slash-right-4": [Hitbox(Position(50, 31), Dimensions(14, 14))],
                    "slash-right-5": [Hitbox(Position(48, 18), Dimensions(16, 17))],
                },
                actions=_actions_lpc_slash(),
                stack=["shortsword"],
            ),
            "spear": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes=None,
                actions=_actions_lpc_thrust(),
                stack=["spear"],
            ),
            "crossbow": SheetProperties(
                dimensions=lpc_dim,
                hitboxes=None,
                attackboxes=None,
                actions=_actions_lpc_thrust(),
                stack=["crossbow"],
            ),
        },
    )