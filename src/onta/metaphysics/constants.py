from enum import Enum

# TOP LEVEL TYPES
class FormType(Enum):
    TILE = 'tile'
    STRUT = 'strut'
    PLATE = 'plate'
    # TODO: TRACK = 'track'

class EntityType(Enum):
    SPRITE = 'sprite'
    # TODO: PIXIE = 'pixie'
    # TODO: NYMPH = 'nypmh'

class SelfTypes(Enum):
    AVATAR = 'avatar'
    QUALIA = 'qualia'

class DialecticType(Enum):
    PROJECTILE = 'projectile'
    EXPRESSION = 'expression'

# SECOND LEVEL TYPES
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

class AvatarTypes(Enum):
    ARMORY = 'armory'
    EQUIPMENT = 'equipment'
    INVENTORY = 'inventory'
    QUANTITY = 'quantity'

class ApparelTypes(Enum):
    ARMOR = 'armor'
    EQUIPMENT = 'equipment'

# SPECIAL TYPES

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