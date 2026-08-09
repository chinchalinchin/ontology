from typing import Dict

class Device:
    mapping: Dict

    def __init__(self, mapping):
        self.mapping = mapping

class Keyboard(Device):
    pass 

class Controller(Device):
    pass