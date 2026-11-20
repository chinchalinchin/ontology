"""
@domain.test
@test.unit
@app.module
@workflow.combat
@workflow.projectiles

# Ontology: Tests - tests.unit.app.game.logic.relations.test_projectiles

Unit tests for ProjectileIndex.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.relations import ProjectileIndex

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_module,
    pytest.mark.workflow_combat,
    pytest.mark.workflow_projectiles,
]

# -----------------------------------------------------


def test_projectile_index_from_properties_resolves_configured_weapons(
    mock_projectile_index: ProjectileIndex,
):
    """Verifies ProjectileIndex compiled from cursors/main.yaml maps ranged weapons to projectiles."""
    assert mock_projectile_index.resolve("longbow") == "arrow"
    assert mock_projectile_index.resolve("crossbow") == "bolt"
    assert mock_projectile_index.resolve("cannon") == "cannonball"

    # Melee weapons and empty/None keys resolve to None
    assert mock_projectile_index.resolve("sword") is None
    assert mock_projectile_index.resolve("spear") is None
    assert mock_projectile_index.resolve("") is None
    assert mock_projectile_index.resolve(None) is None


def test_projectile_index_from_properties_skips_unbound_projectiles(
    mock_properties_schema,
):
    """Verifies projectiles without a weapon binding are omitted from the index."""
    projectiles = mock_properties_schema.cursors.projectiles
    projectiles["cannonball"].weapon = None

    index = ProjectileIndex.from_properties(projectiles)

    assert index.resolve("cannon") is None
    assert index.resolve("longbow") == "arrow"
    assert index.resolve("crossbow") == "bolt"


def test_projectile_index_register_and_idempotent_rebind(
    mock_projectile_index: ProjectileIndex,
):
    """Verifies explicit registration and idempotent re-registration of identical bindings."""
    mock_projectile_index.register("shortbow", "arrow")
    assert mock_projectile_index.resolve("shortbow") == "arrow"

    # Identical binding succeeds without raising
    mock_projectile_index.register("shortbow", "arrow")
    assert mock_projectile_index.resolve("shortbow") == "arrow"


def test_projectile_index_conflicting_weapon_binding_raises(
    mock_projectile_index: ProjectileIndex,
):
    """Verifies binding an already-mapped weapon to a different projectile raises ValueError."""
    with pytest.raises(ValueError, match="already bound"):
        mock_projectile_index.register("longbow", "bolt")


def test_projectile_index_init_accepts_relations_dict():
    """Verifies direct dictionary initialization populates lookup mappings."""
    index = ProjectileIndex({"longbow": "arrow", "crossbow": "bolt"})

    assert index.resolve("longbow") == "arrow"
    assert index.resolve("crossbow") == "bolt"
    assert index.resolve("sword") is None