
import munch

import onta.world as world

def generate_player_template(
    game_world: world.World,
) -> str:
    return f"""
        <h3>Player State</h3>
        <ul>
            <li>player.frame: {game_world.hero.frame}</li>
            <li>player.intent: {game_world.hero.intent.intention if game_world.hero.intent else 'None'}</li>
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
        <h2>Control State</h2>
        <h3>Action</h3>
        <ul>
            <li>controls.slash: {user_input.slash}</li>
            <li>controls.thrust: {user_input.thrust}</li>
            <li>controls.shoot: {user_input.shoot}</li>
            <li>controls.cast: {user_input.cast}</li>
        </ul>
    """