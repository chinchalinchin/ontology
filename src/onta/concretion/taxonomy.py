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
    MOVEABLE = 'moveable'
class QualiaFamilies(Enum):
    SIMPLE = 'simple'
    ROTATABLE = 'rotatable'
    STATEFUL = 'stateful'
    PIECEWISE = 'piecewise'
    PIECEWISE_STATEFUL = 'piecewise_stateful'
######## SECOND LEVEL
    # FUNCTIONAL PLATE FAMILIES 
class MoveablePlateFamily(Enum):
    MASS = 'mass'
class StaticPlateFamily(Enum):
    DOOR = 'door'
class SwitchPlateFamily(Enum):
    CONTAINER = 'container'
    PRESSURE = 'pressure'
    GATE = 'gate'
    # DEFINTIONAL QUALIA FAMILIES
class SimpleQualiaFamily(Enum):
    WALLET = 'wallet'
    CONCEPT = 'concept'
    CONCEPTION = 'conception'
class StatefulQualiaFamily(Enum):
    SLOT = 'slot'
class RotatableQualiaFamily(Enum):
    CAP = 'cap'
    BUFFER = 'buffer'
class PiecewiseQualiaFamily(Enum):
    BAG = 'bag'
    BELT = 'belt'
class PiecewiseStatefulQualiaFamily(Enum):
    IDEA = 'idea'
    BAUBLE = 'bauble'

#### PARTITIONS
###### TOP LEVEL
class QualiaPartitions(Enum):
    PACK = 'pack'
    MEASURE = 'measure'
######## SECOND LEVEL
class PackQualiaPartition(Enum):
    BAG = 'bag'
    BELT = 'belt'
    WALLET = 'wallet'
class MeasureQualiaPartition(Enum):
    MIRROR = "mirror"
    METER = "meter"

#### GROUPS
class SlotGroup(Enum):
    CAP = 'cap'
    BUFFER = 'buffer'
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ACTIVE = 'active'

#### STAGES
class TraversalStage(Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ACTIVE = 'active'
class MeasureStage(Enum):
    UNIT = 'unit'
    EMPTY = 'empty'

## SPRITE CONTROLS
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
