import os
import yaml

import onta.settings as settings

class Conf():
    """
    Configuration is wrapped in the `onta.load.conf.Conf` class so a custom _ontology_ at a different location than the default location can be passed into the engine. This object can be a constructed with a path to that _ontology_ to override the preloaded configuration sets.
    """

    conf_dir = None
    sprite_state_conf = {}
    sprite_property_conf = {}
    sprite_sheet_conf = {}
    strut_property_conf = {}
    strut_sheet_conf = {}
    plate_property_conf = {}
    plate_sheet_conf = {}
    tile_sheet_conf = {}
    control_conf = {}
    interface_conf = {}
    composite_conf = {}
    equipment_con = {}

    def __init__(self, data_dir = settings.DEFAULT_DIR):
        """
        Initializes a `onta.load.conf.Conf` object with the user provided _ontology_ path. If not path is provided, the path defaults to `onta.settings.DEFAULT_DIR`, i.e. the installation's tutorial _ontology_.
        """
        self.conf_dir = os.path.join(data_dir, *settings.CONF_PATH)
    
    def __configuration(self, type_key: str, group_key: str) -> dict:
        """Returns a specific group of configuration from the _data/conf_ directory.

        :param type_key: Type of configuration being retrieved._
        :type obj: str
        :param species: Group of configuraiton being retrieved.
        :type species: str
        :return: Configuration formatted into dictionary.
        :rtype: dict
        """
        conf_path = os.path.join(self.conf_dir, group_key, f'{type_key}.yaml')
        with open(conf_path, 'r') as infile:
            conf = yaml.safe_load(infile)
        return conf

    def _self_configuration(self, type_key: str) -> dict:
        """Returns a specific ty

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Self_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'self')

    def _form_configuration(self, type_key: str) -> dict:
        """Returns a specific type of configuration from the _data/conf/forms_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Form_ configuration formatted into dictionary
        :rtype: dict
        """
        return self.__configuration(type_key, 'forms')


    def _entity_configuration(self, type_key: str) -> dict:
        """Returns a specific type of configuration from the _data/conf/entities_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Entity_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'entities')


    def _dialectic_configuration(self, type_key: str) -> dict:
        """Returns a specific type of configuration from the _data/conf/dialectics_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Dialectic_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'dialectics')


    def load_control_configuration(self):
        """Returns the parsed _Control_ configuration from the _data/conf/self/controls.yaml_ file.

        :return: _Control_ specific configurations.
        :rtype: _type_
        """
        if self.control_conf is None:
            self.control_conf = self._self_configuration('controls')
        return self.control_conf


    def load_interface_configuration(self) -> dict:
        """Returns the parsed _Slot_, _Mirror_, _Pack_ and _Avatar_ (collectively known as the _Interface_) configuration from the _data/conf/self/interface.yaml_ file.

        :return: _Interface_ specific configurations.
        :rtype: dict
        """
        if not self.interface_conf:
            self.interface_conf = self._self_configuration('interface')
        return self.interface_conf


    def load_equipment_configuration(self) -> dict:
        """Returns the parsed _Equipment_ configuration from the _data/conf/self/equipment.yaml_ file.

        :return: _Equipment_ specific configurations
        :rtype: dict
        """
        if not self.equipment_conf:
            self.equipment_conf = self._self_configuration('equipment')
        return self.equipment_conf


    def load_composite_configuration(self) -> dict:
        """Returns the parsed _Composite_ configuration from the _data/conf/forms/composite.yaml_.file.

        :return: _Composite_ specific configurations
        :rtype: dict
        """
        if not self.composite_conf:
            self.composite_conf = self._form_configuration('composite')
        return self.composite_conf


    def load_tile_configuration(self) -> dict:
        """Returns the parsed _Tile_ configuration from the _data/conf/forms/tiles.yaml_ file

        :return: _Tile_ specific configurations
        :rtype: dict
        """

        if not self.tile_sheet_conf:
            self.tile_sheet_conf = self._form_configuration('tiles')
        return self.tile_sheet_conf


    def load_sprite_configuration(self) -> tuple:
        """Returns the parsed _Sprite_ configuration from the _data/conf/entities/sprites.yaml_ file.

        :return: _Sprite_ specific configurations parsed into `(sprite_state_conf, sprite_property_conf, sprite_sheet_conf)`-tuple
        :rtype: tuple

        .. note:
            The _Sprite_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class uses the property and state information to manage _Sprite_ states. The `onta.load.repo.Repo` class uses the state and sheet information to load the spritesheets into memory.
        """    
        if not self.sprite_state_conf or not self.sprite_property_conf \
            or not self.sprite_sheet_conf:

            sprites_conf = self._entity_configuration('sprites')

            for sprite_key, sprite_conf in sprites_conf.items():
                self.sprite_property_conf[sprite_key] = sprite_conf['properties']
                self.sprite_sheet_conf[sprite_key] = sprite_conf['sheets']
                self.sprite_sheet_conf[sprite_key]['size'] = sprite_conf['size']

                self.sprite_state_conf[sprite_key] = {}
                for map in sprite_conf['states']:
                    self.sprite_state_conf[sprite_key][map['state']] = {
                        'frames': map['frames'],
                        'row': map['row']
                    }

        return self.sprite_state_conf, self.sprite_property_conf, self.sprite_sheet_conf


    def load_strut_configuration(self) -> tuple:
        """Returns the parsed _Strut_ configuration from the _data/conf/forms/struts.yaml_ file.

        :return: _Strut_ specific configurations parsed into `(strut_property_conf, strut_sheet_conf)`-tuple.
        :rtype: tuple

        .. note::
            The _Strut_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class use the property information to determine how _Strut_\s react to _Sprite_ states. The `onta.load.repo.Repo` class uses the sheet infromation to load the strutsheet into memory.
        .. note::
            Both `onta.world.World` and `onta.load.repo.Repo` require the dimensions of a _Strut_, e.g. its (_w_, _h_) tuple, for calculations. Rather than dispensing with the separation between sheet and property configuration, this value is added to both configuration dictionary. A little bit of redundancy can be a good thing...
        """
        if not self.strut_property_conf or not self.strut_sheet_conf:
            struts_conf = self._form_configuration('struts')

            for strut_key, strut_conf in struts_conf.items():
                self.strut_property_conf[strut_key] =  strut_conf['properties']
                self.strut_property_conf[strut_key]['size'] = strut_conf['size'] 
                self.strut_sheet_conf[strut_key] = {
                    key: val for key, val in strut_conf.items()
                    if key != 'properties'
                }

        return self.strut_property_conf, self.strut_sheet_conf


    def load_plate_configuration(self) -> tuple:
        """Returns the parsed _Plate_ configuration from the _data/conf/forms/plate.yaml_ file. 

        :return: _Plate_ specific configurations parsed into `(plate_property_conf, strut_sheet_conf)`-tupe.
        :rtype: tuple

        .. note:
        """
        if not self.plate_property_conf or not self.plate_sheet_conf:
            plates_conf = self._form_configuration('plates')

            for plate_key, plate_conf in plates_conf.items():
                self.plate_property_conf[plate_key] = plate_conf['properties']
                self.plate_sheet_conf[plate_key] = {
                    key: val for key, val in plate_conf.items()
                    if key != 'properties'
                }
        
        return self.plate_property_conf, self.plate_sheet_conf