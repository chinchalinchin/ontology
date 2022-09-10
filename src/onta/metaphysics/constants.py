from enum import Enum

# CONSTANTS

## TYPE HIERARCHY 
#### FIRST LEVEL TYPES
class OntaType(Enum):
    FORM = 'form'
    ENTITY = 'entity'
    SELF = 'self'
    DIALECTICS = 'dialectics'
###### SECOND LEVEL TYPES
class FormType(Enum):
    TILE = 'tile'
    STRUT = 'strut'
    PLATE = 'plate'
    TRACK = 'track'
    COMPOSITE = 'composite'
class EntityType(Enum):
    SPRITE = 'sprite'
    APPAREL = 'apparel'
    PIXIE = 'pixie'
    NYMPH = 'nypmh'
class SelfType(Enum):
    AVATAR = 'avatar'
    QUALIA = 'qualia'
    WILL = 'will'
class DialecticType(Enum):
    PROJECTILE = 'projectile'
    EXPRESSION = 'expression'
######## THIRD LEVEL TYPES
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
    BELT = 'belt'
    BAG = 'bag'
    CAP = 'cap'
    CONCEPT = 'concept'
    CONCEPTION = 'conception'
    BAUBLE = 'bauble'
    BUFFER = 'buffer'
    IDEA = 'idea'
    MIRROR = 'mirror'
    SLOT = 'slot'
    WALLET = 'wallet'

#### FAMILIES
###### TOP LEVEL
class PlateFamilies(Enum):
    STATIC = 'static'
    SWITCH = 'switch'
    MASS = 'mass'
class QualiaFamilies(Enum):
    SIMPLE = 'simple'
    ROTATABLE = 'rotatable'
    STATEFUL = 'stateful'
    PIECEWISE = 'piecewise'
    PIECEWISE_STATEFUL = 'piecewise_stateful'
    PACK = 'pack'
######## SECOND LEVEL
    ## PLATES
class StaticPlateFamily(Enum):
    DOOR = 'door'
class SwitchPlateFamily(Enum):
    CONTAINER = 'container'
    PRESSURE = 'pressure'
    GATE = 'gate'
    ## QUALIA
class SimpleQualiaFamily(Enum):
    WALLET = 'wallet'
    CONCEPT = 'concept'
    CONCEPTION = 'conception'
class RotatableQualiaFamily(Enum):
    CAP = 'cap'
    BUFFER = 'buffer'
class PiecewiseQualiaFamily(Enum):
    BAG = 'BAG'
    BELT = 'BELT'
class PiecewiseStatefulQualiaFamily(Enum):
    IDEA = 'idea'
    BAUBLE = 'bauble'
class PackQualiaFamily(Enum):
    BAG = 'bag'
    BELT = 'belt'
    WALLET = 'wallet'
class MeasureQualiaFamily(Enum):
    MIRROR = "mirror"
    METER = "meter"

## DECOMPOSITIONS
class SlotPiece(Enum):
    CAP = 'cap'
    BUFFER = 'buffer'
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ACTIVE = 'active'

## CONTROLS
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
