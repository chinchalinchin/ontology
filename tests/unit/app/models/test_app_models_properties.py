"""
# Ontology: tests.unit.test_app_models_properties
"""
from app.models.properties import SheetProperties

from libs.core.models import Hitbox, Position, Dimensions


def test_equipment_attackboxes_instantiate_cython_hitbox():
    """
    Ensure parsed equipment attackbox mappings coerce into instances of libs.core.models.Hitbox.
    """

    hb = Hitbox(Position(46, 44), Dimensions(7, 20))
    props = SheetProperties(
        dimensions=Dimensions(64, 64),
        attackboxes={"slash-right-3": [hb]}
    )

    assert "slash-right-3" in props.attackboxes
    assert len(props.attackboxes["slash-right-3"]) == 1
    attackbox = props.attackboxes["slash-right-3"][0]
    assert isinstance(attackbox, Hitbox)
    assert attackbox.position.x == 46
    assert attackbox.position.y == 44
    assert attackbox.dimensions.w == 7
    assert attackbox.dimensions.l == 20