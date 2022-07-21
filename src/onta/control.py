
from pynput import keyboard

import onta.settings as settings
import onta.util.logger as logger

log = logger.Logger('ontology.onta.control', settings.LOG_LEVEL)

CONTROLS = ['space', 'alt_left', 'ctrl_left', 'shift_left', 'tab', 'up', 'left', 'right', 'down']

class Controller():

    listener = None
    keys = {}

    @staticmethod
    def map_key(key):
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

    def __init__(self, config):
        self.control_conf = config.configuration('controls')
        self.keys = { 
            key: False for key in 
                ['space', 'alt_left', 'ctrl_left', 'shift_left', 
                    'tab', 'up', 'left', 'right', 'down'] 
        }
        self._register_listener()
        self._start_listener()
        
    def _register_listener(self):
        log.debug('Registering keyboard listeners...', 'Controller._register_listener')
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def _start_listener(self):
       self.listener.start()

    def _direction(self):
        directions = self.control_conf['directions']
        direction_flags = {}
        for dir_key, dir_conf in directions.items():
            input_combo = dir_conf['input']
            direction_flags[dir_key] = all(self.keys[key] for key in input_combo)
        return direction_flags

        # TODO: account for overlap in states, i.e. n and nw will be triggered at same time...


    def _actions(self):
        actions = self.control_conf['actions']
        action_flags = {}
        for action_key, action_conf in actions.items():
            input_combo = action_conf['input']
            action_flags[action_key] = all(self.keys[key] for key in input_combo)
        return action_flags 


    def on_press(self, key):
        self.keys[self.map_key(key)] = True
    
    def on_release(self, key):
        self.keys[self.map_key(key)] = False

    def poll(self):
        user_input = self._direction()
        user_input.update(self._actions())
        return user_input
