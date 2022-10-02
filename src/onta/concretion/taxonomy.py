from enum import Enum

# Onta Taxonomy
# The Enums below enumerate (imagine that) the network of sets that constitute the various permutations of a given _ontology_.

## TYPE HIERARCHY 
#   _Types_ are the central _Onta_ hierarchy of "being", from which all other abstract sets are derived. The elements in this hierarchy are actual, existent in-game objects with on-screen representations.
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
# _Families_ are abstractions on top of the concrete _Types_. They represent ways of grouping the _Types_ by function or definition (i.e. how the asset is extracted from the asset file). Each _Family_ member represents a subset of its parent _Type_.
###### TOP LEVEL
class StrutFamilies(Enum):
    HITBOX = "hitbox"
class PlateFamilies(Enum):
    MOVEABLE = 'moveable'
    STATIC = 'static'
    SWITCH = 'switch'
class QualiaFamilies(Enum):
    PIECEWISE = 'piecewise'
    PIECEWISE_STATEFUL = 'piecewise_stateful'
    ROTATABLE = 'rotatable'
    SIMPLE = 'simple'
    STATEFUL = 'stateful'
######## SECOND LEVEL
    # FUNCTIONAL PLATE FAMILIES 
class MoveablePlateFamily(Enum):
    MASS = 'mass'
class StaticPlateFamily(Enum):
    DOOR = 'door'
class SwitchPlateFamily(Enum):
    CONTAINER = 'container'
    GATE = 'gate'
    PRESSURE = 'pressure'
    # DEFINTIONAL QUALIA FAMILIES
class SimpleQualiaFamily(Enum):
    CONCEPT = 'concept'
    CONCEPTION = 'conception'
    WALLET = 'wallet'
class StatefulQualiaFamily(Enum):
    SLOT = 'slot'
class RotatableQualiaFamily(Enum):
    BUFFER = 'buffer'
    CAP = 'cap'
class PiecewiseQualiaFamily(Enum):
    BAG = 'bag'
    BELT = 'belt'
class PiecewiseStatefulQualiaFamily(Enum):
    BAUBLE = 'bauble'
    IDEA = 'idea'

#### PARTITIONS
# A _Partition_ is similar to a _Family_, in that it is an abstract grouping of _Types_, but a _Partition_ does not denote a functional or definitional grouping, but rather a purely visual (or aesthetic, for the philosophically minded) grouping of elements. For example, a _Pack_ qualia is just the on-screen grouping of the _Belt_ and _Bag_ qualia, i.e. an abstraction of the latter two _Quales_ into a higher level _Quale_, useful for the rendering engine so that it need not focus on minute details.
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

#### QUALIA STATE DEFINITIONS
# a _Stateful_ enum denotes the possible states for a given _Stateful Qualia_. A qualia can either be 'traversed', in which case it cycles through the phases: `enabled`, `active`, `disabled`, or it can be 'measure' a player property, like health or magic. 
class StatefulQualiaTraversal(Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ACTIVE = 'active'
class StatefulQualiaMeasure(Enum):
    UNIT = 'unit'
    EMPTY = 'empty'

#### SPRITE PROPERTIES
###### FIRST LEVEL
class SpriteProperty(Enum):
    POSITION = "position"
    STATURE = "stature"
    INTENT = "intent"
    FRAME = "frame"
    LAYER = "layer"
    PLOT = "plot"
    SLOT = "slot"
    ARMOR = "armor"
    SHIELD = "shield"
    PACK = "pack"
    HEALTH = "health"
    MEMORY = "memory"
    DESIRES = "desires"
    CAPITAL = "capital"
######## SECOND LEVEL
class CapitalProperty(Enum):
    WALLET = "wallet"
    EQUIPMENT = "equipment"
    ARMORY = "armory"
    INVENTORY = "inventory"
    RESOURCES = "resources"
class MemoryProperty(Enum):
    PATHS = "paths"
    INTENT = "intent"
class StatureProperty(Enum):
    DISPOSITION = "disposition"
    ATTENTION = "attention"
    INTENTION = "intention"
    EXPRESSION = "expression"
    DIRECTION = "direction"
    ACTION = "action"
class SlotProperty(Enum):
    CAST = "cast"
    THRUST = "thrust"
    SLASH = "slash"
    SHOOT = "shoot"
class PackProperty(Enum):
    BAG = "bag"
    BELT = "belt"
class HealthProperty(Enum):
    CURRENT = "current"
    MAX = "max"

#### SPRITE CONTROLS
class DesireControl(Enum):
    APPROACH = 'approach'
    FLEE = 'flee'
    ENGAGE = 'engage'
class IntentionControl(Enum):
    MOVE = 'move'
    COMBAT = 'combat'
    DEFEND = 'defend'
    EXPRESS = 'express'
    OPERATE = 'operate'

#### STYLE ATTRIBUTES
class StyleAttribte(Enum):
    pass

#### CONSTANTS
class Constants(Enum):
    SIZE = "size"
    UNITS = "units"
    X_COORD = "x"
    Y_COORD = "y"
    HEIGHT = "height"
    WIDTH = "width"
