from enum import Enum

#### FIRST LEVEL TYPES
class OntaTypes(Enum):
    FORM = 'form'
    ENTITY = 'entity'
    SELF = 'self'
    DIALECTICS = 'dialectics'

#### SECOND LEVEL TYPES
class FormType(Enum):
    TILE = 'tile'
    STRUT = 'strut'
    PLATE = 'plate'
    # TODO: TRACK = 'track'
    COMPOSITE = 'composite'

class EntityType(Enum):
    SPRITE = 'sprite'
    APPAREL = 'apparel'
    # TODO: PIXIE = 'pixie'
    # TODO: NYMPH = 'nypmh'

class SelfType(Enum):
    AVATAR = 'avatar'
    QUALIA = 'qualia'
    WILL = 'will'

class DialecticType(Enum):
    PROJECTILE = 'projectile'
    EXPRESSION = 'expression'

#### THIRD LEVEL TYPES
class PlateType(Enum):
    DOOR = 'door'
    CONTAINER = 'container'
    GATE = 'gate'
    PRESSURE = 'pressure'
    MASS = 'mass'

class AvatarType(Enum):
    ARMORY = 'armory'
    EQUIPMENT = 'equipment'
    INVENTORY = 'inventory'
    QUANTITY = 'quantity'

class ApparelType(Enum):
    ARMOR = 'armor'
    EQUIPMENT = 'equipment'
    SHIELD = 'shield'

#### FOURTH LEVEL TYPES
class ExtrinsicType(Enum):
    PACK = 'pack'
    BAG = 'bag'
    WALLET = 'wallet'
    SLOT = 'slot'
    MIRROR = 'mirror'

class IntrinsicType(Enum):
    IDEA = 'idea'
    BAUBLE = 'bauble'
    CONCEPT = 'concept'
    CONCEPTION = 'conception'
    ASIDE = 'aside'
    FOCUS = 'focus'

#### FIFTH LEVEL TYPES
class PackType(Enum):
    BAG = 'bag'
    BELT = 'belt'

class MirrorType(Enum):
    LIFE = 'life'
    MAGIC = 'magic'


### DEPENDENT TYPES
class StaticPlateType(Enum):
    DOOR = 'door'

class SwitchPlateType(Enum):
    CONTAINER = 'container'
    PRESSURE = 'pressure'
    GATE = 'gate'

class PiecewiseQualiaType(Enum):
    MIRROR = 'mirror'
    PACK = 'pack'
    IDEA = 'idea'
    BAUBLE = 'bauble'
    ASIDE = 'aside'
    FOCUS = 'focus'

class StyledQualiaType(Enum):
    SLOT = 'slot'

class SimpleQualiaType(Enum):
    CONCEPT = 'concept'
    CONCEPTION = 'conception'

class DirectionalQualiaPiece(Enum):
    CAP = 'cap'

class AlignmentQualiaPiece(Enum):
    BUFFER = 'buffer'

## DECOMPOSITIONS
class SlotPiece(Enum):
    CAP = 'cap'
    BUFFER = 'buffer'
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ACTIVE = 'active'

## OTHER
class Desires(Enum):
    APPROACH = 'approach'
    FLEE = 'flee'
    ENGAGE = 'engage'

class Intentions(Enum):
    MOVE = 'move'
    COMBAT = 'combat'
    DEFEND = 'defend'
    EXPRESS = 'express'
    OPERATE = 'operate'
