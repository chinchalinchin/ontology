import onta.settings as settings
import onta.engine.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)

def detect_collision(sprite_hitbox, hitbox_list):
    for hitbox in hitbox_list:
        if hitbox is not None and calculator.intersection(sprite_hitbox, hitbox):
            # return true once collision is detected. it doesn't matter where it occurs, only what direction the hero is travelling...
            log.verbose(f'Detected sprite hitbox {sprite_hitbox} collision with hitbox at {hitbox}', 
                'detect_collision')
            return True

def recoil_sprite(sprite, sprite_props):
    # TODO: pass in collide directly instead of through dictionary
    if 'down' in sprite['state']:
        sprite['position']['y'] -= sprite_props['collide']
    elif 'left' in sprite['state']:
        sprite['position']['x'] -= sprite_props['collide']
    elif 'right' in sprite['state']:
        sprite['position']['x'] += sprite_props['collide']
    else:
        sprite['position']['y'] += sprite_props['collide']

def generate_collision_map(npcs, villains):
    collision_map = { 
        npc_key: {
            vil_key: False for vil_key in villains.keys()
        } for npc_key in npcs.keys()
    }
    collision_map.update({
        vil_key: {
            npc_key: False for npc_key in npcs.keys()
        } for vil_key in villains.keys()
    })
    return collision_map