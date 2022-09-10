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

class QualiaType(Enum):
    CAP = 'cap'
    BELT = 'belt'
    BAG = 'bag'
    BUFFER = 'buffer'
    WALLET = 'wallet'
    SLOT = 'slot'
    MIRROR = 'mirror'
    IDEA = 'idea'
    BAUBLE = 'bauble'
    CONCEPT = 'concept'
    CONCEPTION = 'conception'

#### FOURTH LEVEL TYPES
class PackType(Enum):
    BAG = 'bag'
    BELT = 'belt'

class MirrorType(Enum):
    LIFE = 'life'
    MAGIC = 'magic'

### OVERLAPPING TYPES
class StaticPlateType(Enum):
    DOOR = 'door'

class SwitchPlateType(Enum):
    CONTAINER = 'container'
    PRESSURE = 'pressure'
    GATE = 'gate'

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
