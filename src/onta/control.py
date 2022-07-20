
from pynput import keyboard

import onta.load.conf as conf

def poll() -> dict:
    return {}

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
                return 'shft_left'
            if key == keyboard.Key.tab:
                return 'tab'
            if key == keyboard.Key.up:
                return 'up'
            if key == keyboard.Key.left:
                return 'left'
            if key == keyboard.Key.right:
                return 'right'
            if key == keyboard.down:
                return 'down'
            return 'unmapped'

    def __init__(self):
        self.control_conf = conf.configuration('controller')
        self._register_listener()
        self._start_listener()

    def _register_listener(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def _start_listener(self):
       self.listener.start()

    def _direction(self):
        directions = self.control_conf['directions']
        for dir_key, dir_conf in directions.items():
            pass

    def _actions(self):
        pass

    def on_press(self, key):
        self.keys[self.map_key(key)] = True
        if key == keyboard.Key.space:
            print('space pressed')
        pass
    
    def on_release(self, key):
        self.keys[self.map_key(key)] = False
        if key == keyboard.Key.space:
            print('space released')
        pass

    def poll(self):
        self._direction()
        self._actions()
