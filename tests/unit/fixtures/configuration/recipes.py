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
                animation=AnimationRecipe.NONE.value
            ),
            fore=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        cursors=CursorRecipe(
            projectiles=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            expressions=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        crafts=CraftRecipe(
            struts=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            bridges=Recipe(
                frame=FrameRecipe.ORIENTED.value,
                animation=AnimationRecipe.NONE.value
            )
        ),
        effects=EffectRecipe(
            collectables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            hazards=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            passive=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            reactables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            fluids=Recipe(
                frame=FrameRecipe.FLUID.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            )
        ),
        objects=ObjectRecipe(
            chests=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value
            ),
            crates=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            doors=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            gates=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value
            ),
            plates=Recipe(
                frame=FrameRecipe.ITERABLE, 
                animation=AnimationRecipe.BINARY.value
            ),
            signs=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        sheets=SheetRecipe(
            sprites=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value
            ),
            players=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value
            ),
            pixies=Recipe(
                frame=FrameRecipe.STATE.value, 
                animation=AnimationRecipe.STATE.value
            )
        ),
        resources=ResourceRecipe(
            trees=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value
            ),
            ore=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value
            ),
            crops=Recipe(
                frame=FrameRecipe.STAGE.value,
                animation=AnimationRecipe.NONE.value
            )
        ),
        widgets=WidgetRecipe(
            pages=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            buttons=Recipe(
                frame=FrameRecipe.TRAVERSAL.value, 
                animation=AnimationRecipe.TRAVERSAL.value
            ),
            meters=Recipe(
                frame=FrameRecipe.METER.value, 
                animation=AnimationRecipe.METER.value
            ),
            panes=Recipe(
                frame=FrameRecipe.NONE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            icons=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        geography=GeographyRecipe(
            shorelines=Recipe(
                frame=FrameRecipe.CARDINAL.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
    )

