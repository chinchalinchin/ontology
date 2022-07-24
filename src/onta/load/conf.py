import os
import yaml

class Conf():
    """
    
    Configuration is wrapped in the `onta.load.conf.Conf` class so a custom _ontology_ at a different location than the default location can be passed into the engine. This object can be a constructed with a path to that _ontology_ to override the preloaded configuration sets.
    """

    conf_dir = None
    sprite_state_conf = None
    sprite_property_conf = None
    sprite_sheet_conf = None
    strut_property_conf = None
    strut_sheet_conf = None
    plate_property_conf = None
    plate_sheet_conf = None
    tile_sheet_conf = None
    control_conf = None

    def __init__(self, data_dir):
        """
        
        """
        self.conf_dir = os.path.join(data_dir, 'conf')
    
    def _configuration(self, obj: str) -> dict:
        conf_path = os.path.join(self.conf_dir, f'{obj}.yaml')
        with open(conf_path, 'r') as infile:
            conf = yaml.safe_load(infile)
        return conf

    def load_control_configuration(self):
        if self.control_conf is None:
            self.control_conf = self._configuration('controls')
        return self.control_conf

    def load_tile_configuration(self):
        if self.tile_sheet_conf is None:

            tiles_conf = self._configuration('tiles')
            self.tile_sheet_conf = { }
            for tile_key, tile_conf in tiles_conf.items():
                self.tile_sheet_conf[tile_key] = tile_conf['image']

        return self.tile_sheet_conf

    def load_sprite_configuration(self) -> tuple:
        """ Returns `(sprite_state_conf, sprite_property_conf, sprite_sheet_conf)`-tuple
        :type self:
        :param self:
        :rtype: tuple
        """    
        if self.sprite_state_conf is None \
            or self.sprite_property_conf is None\
            or self.sprite_sheet_conf is None:

            sprites_conf = self._configuration('sprites')

            self.sprite_state_conf = { }
            self.sprite_property_conf = { }
            self.sprite_sheet_conf = { }

            for sprite_key, sprite_conf in sprites_conf.items():
                self.sprite_state_conf[sprite_key] = {}
                self.sprite_property_conf[sprite_key] = {}
                self.sprite_sheet_conf[sprite_key] = {}

                self.sprite_property_conf[sprite_key] = sprite_conf['properties']
                self.sprite_sheet_conf[sprite_key] = sprite_conf['sheets'] 
                for map in sprite_conf['states']:
                    self.sprite_state_conf[sprite_key][map['state']] = {}
                    self.sprite_state_conf[sprite_key][map['state']]['frames'] = map['frames']
                    self.sprite_state_conf[sprite_key][map['state']]['row'] = map['row']

        return self.sprite_state_conf, self.sprite_property_conf, self.sprite_sheet_conf

    def load_strut_configuration(self) -> tuple:
        """ Description
        :type self:
        :param self:    
        :rtype: dict
        """
        if self.strut_property_conf is None \
            or self.strut_sheet_conf is None:
            struts_conf = self._configuration('struts')

            self.strut_property_conf = {}
            self.strut_sheet_conf = {}
            for strut_key, strut_conf in struts_conf.items():
                self.strut_property_conf[strut_key] = {}
                self.strut_sheet_conf[strut_key] = {} 
                self.strut_property_conf[strut_key] = strut_conf['properties']
                self.strut_sheet_conf[strut_key] = strut_conf['image']
        return self.strut_property_conf, self.strut_sheet_conf

    def load_plate_configuration(self) -> tuple:
        if self.plate_property_conf is None \
            or self.plate_sheet_conf is None:
            plates_conf = self._configuration('plates')

            self.plate_property_conf = {}
            self.plate_sheet_conf = {}
            for plate_key, plate_conf in plates_conf.items():
                self.plate_property_conf[plate_key] = {}
                self.plate_sheet_conf[plate_key] = {}
                self.plate_property_conf[plate_key] = plate_conf['properties']
                self.plate_sheet_conf[plate_key] = plate_conf['image']
        
        return self.plate_property_conf, self.plate_sheet_conf