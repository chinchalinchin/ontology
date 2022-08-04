import onta.settings as settings
import onta.util.logger as logger


log = logger.Logger('onta.engine.logic', settings.LOG_LEVEL)


def determine_actionable_states(
    sprite: dict,
    equipment_config: dict
) -> list:
    actionable_states = []
    for equip_key, equip_flag in sprite['inventory']['equipment'].items():
        if equip_flag:
            for state in equipment_config[equip_key]['animate_states']:
                actionable_states.append(state)
    return actionable_states