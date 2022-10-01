import functools
import munch
from typing \
    import Any, Literal, Union
from pynput import keyboard

from onta.metaphysics \
    import settings, logger
from onta.actuality \
    import conf

log = logger.Logger(
    'onta.will', 
    settings.LOG_LEVEL
)


@functools.lru_cache(maxsize=15)
def map_key(
    key: Any
) -> Union[
    str,
    Literal["space"],
    Literal["alt_left"],
    Literal["ctrl_left"],
    Literal["shift_left"],
    Literal["tab"],
    Literal["up"],
    Literal["down"],
    Literal["right"],
    Literal["down"]
]:
    try:
        char_pressed = key.char
        return char_pressed
    except AttributeError:
        if key == keyboard.Key.space:
            return 'space'
        if key == keyboard.Key.alt_l:
            return 'alt_left'
        if key == keyboard.Key.ctrl_l:
            return 'ctrl_left'
        if key == keyboard.Key.shift_l:
            return 'shift_left'
        if key == keyboard.Key.tab:
            return 'tab'
        if key == keyboard.Key.up:
            return 'up'
        if key == keyboard.Key.left:
            return 'left'
        if key == keyboard.Key.right:
            return 'right'
        if key == keyboard.Key.down:
            return 'down'
        return 'unmapped'

class Will():

    def __init__(
        self, 
        ontology_path = settings.DEFAULT_DIR
    ) -> None:
        self.control_conf = conf.Conf(ontology_path).load_will_configuration()
        self.keys = munch.munchify({ 
            key: False 
            for key 
            in self.control_conf.valid
        })
        self._register_listener()
        self._start_listener()
        

    def _on_press(
        self, 
        key
    ) -> None:
        setattr(
            self.keys, 
            map_key(key), 
            True
        )
        
            
    def _on_release(
        self, 
        key
    ) -> None:
        setattr(
            self.keys,
            map_key(key), 
            False
        )


    def _register_listener(
        self
    ) -> None:
        log.debug(
            'Registering keyboard listeners...', 
            'Will._register_listener'
        )
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )

    def _start_listener(
        self
    ) -> None:
       self.listener.start()

    # TODO: _directions, _actions and _meditatiosn are the exact same form...
    #           CANDIDATE FOR REFACTORING...

    def _direction(
        self
    ) -> munch.Munch:
        directions = self.control_conf.directions
        direction_flags, dirs = {}, 0

        for dir_key, dir_conf in directions.items():
            input_combo = dir_conf.input
            direction_flags[dir_key] = all(
                self.keys.get(key) 
                for key 
                in input_combo
            )
            if direction_flags[dir_key]:
                dirs += 1

        activated_key = None

        if dirs == 1:
            activated_key = [
                dir_key 
                for dir_key, dir_flag 
                in direction_flags.items()
                if dir_flag
            ][-1]

        if dirs > 1:
            precedence = 0
            for dir_key, dir_flag in direction_flags.copy().items():
                if dir_flag and \
                    directions.get(dir_key).precedence >= precedence:

                    precedence = directions.get(dir_key).precedence
                    activated_key = dir_key

        return munch.Munch({ 
            key: True 
            if key == activated_key 
            else False 
            for key 
            in direction_flags.keys() 
        })

    def _actions(
        self
    ) -> munch.Munch:
        actions = self.control_conf.actions
        action_flags, acts = {}, 0
        for action_key, action_conf in actions.items():
            input_combo = action_conf.input
            action_flags[action_key] = all(
                self.keys.get(key) 
                for key 
                in input_combo
            )
            if action_flags[action_key]:
                acts += 1

        activated_key = None

        if acts == 1:
            activated_key = [
                act_key 
                for act_key, act_flag
                in action_flags.items()
                if act_flag
            ][-1]

        if acts > 1:
            precedence = 0
            for act_key, act_flag in action_flags.copy().items():
                if act_flag and \
                    actions.get(act_key).precedence >= precedence:

                    precedence = actions.get(act_key).precedence
                    activated_key = act_key
               
        return munch.Munch({ 
            key: True 
            if key == activated_key 
            else False 
            for key 
            in action_flags.keys() 
        }) 

    def _meditations(
        self
    ) -> munch.Munch:
        meditations = self.control_conf.meditations
        med_flags, meds = {}, 0

        for med_key, med_conf in meditations.items():
            input_combo = med_conf.input
            med_flags[med_key] = all(
                self.keys.get(key) 
                for key 
                in input_combo
            )
            if med_flags[med_key]:
                meds += 1

        activated_key = None

        if meds == 1:
            activated_key = [
                med_key
                for med_key, med_flag
                in med_flags.items()
                if med_flag
            ][-1]

        elif meds > 1:
            precedence = 0
            for med_key, med_flag in med_flags.copy().items():
                if med_flag and \
                    meditations.get(med_key).precedence >= precedence:

                    precedence = meditations.get(med_key).precedence
                    activated_key = med_key

        return munch.Munch({
                key: True 
                if key == activated_key 
                else False 
                for key 
                in med_flags.keys()
            })


    def consume(
        self,
        paused: bool
    ) -> tuple:
        """_summary_

        :return: _description_
        :rtype: munch.Munch

        .. note::
            Both directions, actions and expression can be enabled simultaneously, but within each grouping there can only be one enabled control.
        """
        game_input = self._direction()

        if paused:
            # create menu_input before game_input gets updated with actions
            menu_input = game_input.copy()
            menu_input.update(self._meditations())

        game_input.update(self._actions())

        # there is an inherent assumption in this loop that directions are not consumable.
        #   is that what you want?
        for consume in self.control_conf.consumable:
            if not paused and game_input.get(consume):
                log.debug(
                    f'Consuming {consume} world input', 
                    'Will.consume'
                )
                for input in self.control_conf.actions.get(consume).input:
                    setattr(self.keys, input, False)

            if paused and menu_input.get(consume):
                log.debug(
                    f'Consuming {consume} menu input', 
                    'Will.consume'
                )
                for input in self.control_conf.meditations.get(consume).input:
                    setattr(self.keys, input, False)

        if paused:
            return (
                game_input, 
                menu_input
            )
            
        return (
            game_input, 
            None
        )


    def consume_all(
        self
    ) -> munch.Munch:
        """_summary_

        :return: _description_
        :rtype: munch.Munch

        .. note::
            There is no recursion/nesting in `self.keys`, so just instantiate a `munch.Munch` with one level of keys to avoid recursively `munch.munchify` issue.
        """
        self.keys = munch.Munch({ 
            key: False 
            for key 
            in self.control_conf.valid
        })
        

    def poll(self, paused) -> tuple:
        return self.consume(paused)