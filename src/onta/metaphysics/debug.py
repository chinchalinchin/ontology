
import munch

from onta \
    import world

def generate_player_template(
    game_world: world.World,
) -> str:
    npc_str = ""
    for npc_key, npc in game_world.npcs.items():
        npc_str += f"<h5>{npc_key}</h5>\n"
        npc_str += "<ul style=\"font-size:small\">\n"
        npc_str += f"<li>sprite.frame: {npc.frame}</li>\n"
        npc_str += f"<li>sprite.stature.attention: {npc.stature.attention}</li>\n"
        npc_str += f"<li>sprite.stature.disposition: {npc.stature.disposition}</li>"
        npc_str += f"<li>sprite.stature.intention: {npc.stature.intention}</li>\n"
        npc_str += f"<li>sprite.stature.action: {npc.stature.action}</li>\n"
        npc_str += f"<li>sprite.stature.direction: {npc.stature.direction}</li>\n"
        npc_str += f"<li>sprite.stature.expression: {npc.stature.expression}</li>\n"
        npc_str += "</ul>\n"

    player_str = f"""
        <h5>Player</h5>
        <ul style="font-size: small">
            <li>player.frame: {game_world.hero.frame}</li>
            <li>player.stature.intention: {game_world.hero.stature.intention}</li>
            <li>player.stature.action: {game_world.hero.stature.action}</li>
            <li>player.stature.direction: {game_world.hero.stature.direction}</li>
            <li>player.stature.expression: {game_world.hero.stature.expression}</li>
        </ul>
    """
    if npc_str:
        return f"""
            {player_str}
            {npc_str}
        """
    return player_str

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

    projectile_str = ""
    if game_world.projectiles:
        for i, p in enumerate(game_world.projectiles):
            projectile_str += f'<li> world.projectiles[{i}].current: {p.current}</li>\n'

    if enabled_switch_str:
        if projectile_str:
            return f"""
            <h5>World</h5>
            <ul style="font-size: small">    
                {enabled_switch_str}
                {projectile_str}
            </ul>
            """
        return f"""
        <h5>World</h5>
        <ul style="font-size: small">    
            {enabled_switch_str}
        </ul>
        """
    return f"""
    <h5>World</h5>
    """