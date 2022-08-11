
import munch

import onta.world as world

def generate_player_template(
    game_world: world.World,
) -> str:
    return f"""
        <h5>Player</h5>
        <ul style="font-size: small">
            <li>player.frame: {game_world.hero.frame}</li>
            <li>player.stature.intention: {game_world.hero.stature.intention}</li>
            <li>player.stature.action: {game_world.hero.stature.action}</li>
            <li>player.stature.direction: {game_world.hero.stature.direction}</li>
            <li>player.stature.expression: {game_world.hero.stature.expression}</li>
        </ul>
    """

def generate_input_template(
    user_input: munch.Munch
) -> str:
    return f"""
        <h5>Controls</h5>
        <ul style="font-size: small">
            <li>controls.slash: {user_input.slash}</li>
            <li>controls.thrust: {user_input.thrust}</li>
            <li>controls.shoot: {user_input.shoot}</li>
            <li>controls.cast: {user_input.cast}</li>
            <li>controls.up: {user_input.up}</li>
            <li>controls.left: {user_input.left}</li>
            <li>controls.down: {user_input.down}</li>
            <li>controls.right: {user_input.right}</li>
        </ul>
    """

def generate_world_template(
    game_world: world.World
) -> str:

    enabled_switches = {}
    for switch_key, switch_indices in game_world.switch_map.get(game_world.layer).items():
        for switch_index, switch_flag in switch_indices.items():
            if switch_flag:
                enabled_switches[switch_key] = switch_index

    enabled_switch_str = ""
    for key, ind in enabled_switches.items():
        enabled_switch_str += f"<li> world.switch_map: {key}({ind})</li>\n"

    if enabled_switch_str:
        return f"""
        <h5>World</h5>
        <ul style="font-size: small">    
            {enabled_switch_str}
        </ul>
        """
    return f"""
    <h5>World</h5>
    """