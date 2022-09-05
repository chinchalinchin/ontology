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

class SelfTypes(Enum):
    AVATAR = 'avatar'
    QUALIA = 'qualia'
    WILL = 'will'

class DialecticType(Enum):
    PROJECTILE = 'projectile'
    EXPRESSION = 'expression'

#### THIRD LEVEL TYPES
class PlateTypes(Enum):
    DOOR = 'door'
    CONTAINER = 'container'
    GATE = 'gate'
    PRESSURE = 'pressure'
    MASS = 'mass'

class AvatarTypes(Enum):
    ARMORY = 'armory'
    EQUIPMENT = 'equipment'
    INVENTORY = 'inventory'
    QUANTITY = 'quantity'

class ApparelTypes(Enum):
    ARMOR = 'armor'
    EQUIPMENT = 'equipment'

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

#### DEPENDENT TYPES
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
