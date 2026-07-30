from app.models import Shape
from app.models.properties import CursorProperties

# -------------------------------   Primitive Configuration Levels

class SpriteComposition(BaseModel):
    key: str 
    base: str
    apparel: List[str]
    features: List[str]

# -------------------------------   Intermediate Configuration Levels

class PixieConfiguration(BaseModel):
    shapes: Dict[str, Shape]
    action: Dict[str, PixieAction]

class SpriteConfiguration(BaseModel):
    shape: Shape
    actions: Dict[str, SpriteAction]
    compostions: List[SpriteComposition]

# -------------------------------  

class CursorConfiguration:
    expressions: Dict[str, CursorProperties]
    projectiles: Dict[str, CursorProperties]

# -------------------------------  

class SheetConfiguration(BaseModel):
    pixies: PixieConfiguration
    sprites: SpriteConfiguration