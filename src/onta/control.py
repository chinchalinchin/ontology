import functools
from typing import Any, Literal, Union
import munch
import numba

from pynput import keyboard

import onta.settings as settings
import onta.loader.conf as conf
import onta.util.logger as logger

log = logger.Logger('onta.control', settings.LOG_LEVEL)


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

class Controller():

    listener = None
    keys = munch.Munch({})


    def __init__(
        self, 
        ontology_path = settings.DEFAULT_DIR
    ) -> None:
        self.control_conf = conf.Conf(ontology_path).load_control_configuration()
        self.keys = munch.munchify({ 
            key: False for key in self.control_conf.valid
        })
        self._register_listener()
        self._start_listener()
        

    def _on_press(
        self, 
        key
    ) -> None:
        setattr(self.keys, map_key(key), True)
        
            
    def _on_release(
        self, 
        key
    ) -> None:
        setattr(self.keys, map_key(key), False)


    def _register_listener(
        self
    ) -> None:
        log.debug('Registering keyboard listeners...', 'Controller._register_listener')
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )

    def _start_listener(
        self
    ) -> None:
       self.listener.start()

    def _direction(
        self
    ) -> munch.Munch:
        directions = self.control_conf.directions
        direction_flags, dirs = {}, 0

        for dir_key, dir_conf in directions.items():
            input_combo = dir_conf.input
            direction_flags[dir_key] = all(self.keys.get(key) for key in input_combo)
            if direction_flags[dir_key]:
                dirs += 1

        # ensure precedence is enforced if overlap
        if dirs > 1:
            precedence, activated_key = 0, None
            for dir_key, dir_flag in direction_flags.copy().items():
                if dir_flag and directions.get(dir_key).precedence >= precedence:
                    precedence = directions.get(dir_key).precedence
                    activated_key = dir_key
            direction_flags = munch.Munch({ 
                key: True if key == activated_key else False for key in direction_flags.keys() 
            })
       
        return munch.Munch(direction_flags)

    def _actions(
        self
    ) -> munch.Munch:
        actions = self.control_conf.actions
        action_flags, acts = {}, 0
        for action_key, action_conf in actions.items():
            input_combo = action_conf.input
            action_flags[action_key] = all(self.keys.get(key) for key in input_combo)
            if action_flags[action_key]:
                acts += 1

        # ensure precedence is enforced if overlap
        if acts > 1:
            precedence, activated_key = 0, None
            for act_key, act_flag in action_flags.copy().items():
                if act_flag and actions.get(act_key).precedence >= precedence:
                    precedence = actions.get(act_key).precedence
                    activated_key = act_key
  
            action_flags = { 
                key: True if key == activated_key else False for key in action_flags.keys() 
            }
                        
        return munch.Munch(action_flags) 

    def consume(
        self
    ) -> munch.Munch:
        """_summary_

        :return: _description_
        :rtype: munch.Munch

        .. note::
            Both directions, actions and expression can be enabled simultaneously, but within each grouping there can only be one enabled control.
        """
        user_input = self._direction()
        user_input.update(self._actions())

        for consume in self.control_conf.consumable:
            if user_input.get(consume):
                log.debug(f'Consuming {consume} user input', 'consume')
                for input in self.control_conf.actions.get(consume).input:
                    setattr(self.keys, input, False)
        return user_input


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
            key: False for key in self.control_conf.valid
        })
        

    def poll(self):
        return self.consume()