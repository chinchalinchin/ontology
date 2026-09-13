from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.game.logic.mechanics.spatial.collision import CollisionMechanics
from app.game.logic.mechanics.spatial.combat import CombatMechanics
from app.game.logic.mechanics.spatial.interaction import InteractionMechanics
from app.game.logic.mechanics.spatial.projectile import ProjectileMechanics
from app.game.logic.mechanics.spatial.switch import SwitchMechanics
from app.game.logic.mechanics.spatial.social import SocialMechanics

__all__ = [ 
    'SwitchMechanics', 
    'ProjectileMechanics', 
    'CollisionMechanics',
    'CombatMechanics',
    'InteractionMechanics',
    'SpatialMechanic',
    'SocialMechanics'
]