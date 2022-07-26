
from re import A
from pynput import keyboard

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger

log = logger.Logger('onta.control', settings.LOG_LEVEL)

CONTROLS = ['space', 'alt_left', 'ctrl_left', 'shift_left', 'tab', 'up', 'left', 'right', 'down', 'e']

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

    def __init__(self, ontology_path = settings.DEFAULT_DIR):
        self.control_conf = conf.Conf(ontology_path).load_control_configuration()
        self.keys = { 
            key: False for key in CONTROLS
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
        direction_flags, dirs = {}, 0
        for dir_key, dir_conf in directions.items():
            input_combo = dir_conf['input']
            direction_flags[dir_key] = all(self.keys[key] for key in input_combo)
            if direction_flags[dir_key]:
                dirs += 1

        # ensure precedence is enforced if overlap
        if dirs > 1:
            precedence, activated_key = 0, None
            for dir_key, dir_flag in direction_flags.copy().items():
                if dir_flag and directions[dir_key]['precedence'] >= precedence:
                    precedence = directions[dir_key]['precedence']
                    activated_key = dir_key
            direction_flags = { key: True if key == activated_key else False for key in direction_flags.keys() }
       
        return direction_flags

    def _actions(self):
        actions = self.control_conf['actions']
        action_flags, acts = {}, 0
        for action_key, action_conf in actions.items():
            input_combo = action_conf['input']
            action_flags[action_key] = all(self.keys[key] for key in input_combo)
            if action_flags[action_key]:
                acts += 1

        # ensure precedence is enforced if overlap
        if acts > 1:
            precedence, activated_key = 0, None
            for act_key, act_flag in action_flags.copy().items():
                if act_flag and actions[act_key]['precedence'] >= precedence:
                    precedence = actions[act_key]['precedence']
                    activated_key = act_key
  
            action_flags = { key: True if key == activated_key else False for key in action_flags.keys() }
                        
        return action_flags 

    def _consume(self):
        user_input = self._direction()
        user_input.update(self._actions())

        for consume in self.control_conf['consumable']:
            if user_input[consume]:
                for input in self.control_conf['actions'][consume]['input']:
                    self.keys[input] = False
        return user_input

    def on_press(self, key):
        self.keys[self.map_key(key)] = True
    
    def on_release(self, key):
        self.keys[self.map_key(key)] = False

    def poll(self):
        user_input = self._consume()

        return user_input
