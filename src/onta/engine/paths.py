
import onta.settings as settings
import onta.engine.collisions as collisions
import onta.engine.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.paths', settings.LOG_LEVEL)

def reorient(sprite, hitbox, collision_sets, goal, speed, world_dim) -> None:
    goal_point = (goal['x'], goal['y'])

    new_up = (hitbox[0], hitbox[1] - 2*speed - 1, hitbox[2], hitbox[3])
    new_left = (hitbox[0] - 2*speed - 1, hitbox[1], hitbox[2], hitbox[3])
    new_right = (hitbox[0] + 2*speed + 1, hitbox[1], hitbox[2], hitbox[3])
    new_down = (hitbox[0], hitbox[1] + 2*speed + 1, hitbox[2], hitbox[3])

    up_valid = all(not collisions.detect_collision(new_up, collision_set) for collision_set in collision_sets)
    left_valid = all(not collisions.detect_collision(new_left, collision_set) for collision_set in collision_sets)
    right_valid = all(not collisions.detect_collision(new_right, collision_set) for collision_set in collision_sets)
    down_valid = all(not collisions.detect_collision(new_down, collision_set) for collision_set in collision_sets)

    possibilities = {}

    log.verbose('Determining which directions are valid for reorientation...', 'reorient')

    if up_valid:
        log.verbose('Up valid!', 'reorient')
        possibilities['up'] = calculator.distance(new_up, goal_point)
    if left_valid:
        log.verbose('Left valid!', 'reorient')
        possibilities['left'] = calculator.distance(new_left, goal_point)
    if right_valid:
        log.verbose('Right valid!', 'reorient')
        possibilities['right'] = calculator.distance(new_right, goal_point)
    if down_valid:
        log.verbose('Down valid!', 'reorient')
        possibilities['down'] = calculator.distance(new_down, goal_point)

    least_state, least_state_distance = None, calculator.distance((0,0), world_dim)

    log.verbose(f'Reorientation possibility map: {possibilities}', 'reorient')

    for key, possibility in possibilities.items():
        if possibility < least_state_distance:
            least_state_distance = possibility
            least_state = key

    log.verbose(f'Choice to minimize distance: {least_state}', 'reorient')

    if least_state == 'up':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_up'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_up'
    elif least_state == 'down':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_down'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_down'
    elif least_state == 'left':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_left'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_left'
    elif least_state == 'right':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_right'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_right'

def concat_dynamic_paths(sprite, static_pathset, hero, npcs, vils):
    pathset = static_pathset.copy()
    npc_keys = list(npcs.keys())
    villain_keys = list(vils.keys())

    if sprite['path']['current'] == 'hero':
        pathset['hero'] = {
            'x': hero['position']['x'],
            'y': hero['position']['y']
        }
    elif sprite['path']['current'] in npc_keys:
        pathset[sprite['path']['curent']] = {
            'x': npcs[sprite['path']['current']]['position']['x'],
            'y': npcs[sprite['path']['current']]['position']['y']
        }
    elif sprite['path'] in villain_keys:
        pathset[sprite['path']['current']] = {
            'x': vils[sprite['path']['current']]['position']['x'],
            'y': vils[sprite['path']['current']]['position']['y']
        }
    return pathset

def locate_intent(intent, hero, npcs, villains, paths):
    if intent == 'hero':
        return (hero['position']['x'], hero['position']['y'],)
    elif intent in list(npcs.keys()):
        return (npcs[intent]['position']['x'], npcs[intent]['position']['y'])
    elif intent in list(villains.keys()):
        return (villains[intent]['position']['x'], villains[intent]['position']['y'])
    elif intent in list(paths.keys()):
        return (paths[intent]['x'], paths[intent]['y'])