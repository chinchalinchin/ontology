"""
# Ontology: tests.unit.fixtures.configuration.recipes

Mock Recipe Configuration fixtures
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import ( 
    FrameRecipe,
    AnimationRecipe,
    HitboxRecipe,
)
from app.models.config import (
    RecipeConfiguration,
    CursorRecipe,
    CraftRecipe,
    WidgetRecipe,
    EffectRecipe,
    ObjectRecipe,
    GeographyRecipe,
    SheetRecipe,
    ResourceRecipe,
    TileRecipe,
    Recipe,
)



# --------------------------------------------------------------------------
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------

@pytest.fixture
def mock_recipes_configuration() -> RecipeConfiguration:
    """Complete RecipeConfiguration matching native engine schemas."""
    return RecipeConfiguration(
        tiles=TileRecipe(
            back=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            fore=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            )
        ),
        cursors=CursorRecipe(
            projectiles=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            expressions=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            )
        ),
        crafts=CraftRecipe(
            struts=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            bridges=Recipe(
                frame=FrameRecipe.ORIENTED.value,
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            )
        ),
        effects=EffectRecipe(
            collectables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            hazards=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            passive=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            reactables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            fluids=Recipe(
                frame=FrameRecipe.FLUID.value, 
                animation=AnimationRecipe.LIFECYCLE.value,
                hitbox=HitboxRecipe.DYNAMIC.value
            )
        ),
        objects=ObjectRecipe(
            chests=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            crates=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            doors=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            gates=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            plates=Recipe(
                frame=FrameRecipe.ITERABLE, 
                animation=AnimationRecipe.BINARY.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            signs=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STATIC.value
            )
        ),
        sheets=SheetRecipe(
            sprites=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            players=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value,
                hitbox=HitboxRecipe.STATIC.value
            ),
            pixies=Recipe(
                frame=FrameRecipe.STATE.value, 
                animation=AnimationRecipe.STATE.value,
                hitbox=HitboxRecipe.STATIC.value
            )
        ),
        resources=ResourceRecipe(
            trees=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STAGE.value
            ),
            ore=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STAGE.value
            ),
            crops=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.STAGE.value
            )
        ),
        widgets=WidgetRecipe(
            pages=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            buttons=Recipe(
                frame=FrameRecipe.TRAVERSAL.value, 
                animation=AnimationRecipe.TRAVERSAL.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            meters=Recipe(
                frame=FrameRecipe.METER.value, 
                animation=AnimationRecipe.METER.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            panes=Recipe(
                frame=FrameRecipe.NONE.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            ),
            icons=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.NONE.value
            )
        ),
        geography=GeographyRecipe(
            shorelines=Recipe(
                frame=FrameRecipe.CARDINAL.value, 
                animation=AnimationRecipe.NONE.value,
                hitbox=HitboxRecipe.DYNAMIC.value
            )
        ),
    )

