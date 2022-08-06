import os
import yaml
import munch
import onta.settings as settings

class Conf():
    """
    Configuration is wrapped in the `onta.loader.conf.Conf` class so a custom _ontology_ at a different location than the default location can be passed into the engine. This object can be a constructed with a path to that _ontology_ to override the preloaded configuration sets.
    """

    conf_dir = None
    sprite_size = munch.Munch({})
    sprite_stature_conf = munch.Munch({})
    sprite_property_conf = munch.Munch({})
    sprite_sheet_conf = munch.Munch({})
    strut_property_conf = munch.Munch({})
    strut_sheet_conf = munch.Munch({})
    plate_property_conf = munch.Munch({})
    plate_sheet_conf = munch.Munch({})
    tile_sheet_conf = munch.Munch({})
    control_conf = munch.Munch({})
    sense_conf = munch.Munch({})
    avatar_conf = munch.Munch({})
    composite_conf = munch.Munch({})
    apparel_conf = munch.Munch({})

    def __init__(
        self, 
        data_dir = settings.DEFAULT_DIR
    ) -> None:
        """
        Initializes a `onta.loader.conf.Conf` object with the user provided _ontology_ path. If not path is provided, the path defaults to `onta.settings.DEFAULT_DIR`, i.e. the installation's tutorial _ontology_.
        """
        self.conf_dir = os.path.join(data_dir, *settings.CONF_PATH)
    
    def __configuration(
        self, 
        type_key: str, 
        group_key: str
    ) -> munch.Munch:
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
            conf = munch.munchify(
                yaml.safe_load(infile)
            )
        return conf

    def _self_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific ty

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Self_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'self')

    def _form_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/forms_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Form_ configuration formatted into dictionary
        :rtype: dict
        """
        return self.__configuration(type_key, 'forms')


    def _entity_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/entities_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Entity_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'entities')


    def _dialectic_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/dialectics_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Dialectic_ configuration formatted into dictionary.
        :rtype: dict
        """
        return self.__configuration(type_key, 'dialectics')


    def load_control_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Control_ configuration from the _data/conf/self/controls.yaml_ file.

        :return: _Control_ specific configurations.
        :rtype: _type_
        """
        if len(self.control_conf) == 0:
            self.control_conf = self._self_configuration('controls')
        return self.control_conf


    def load_sense_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Slot_, _Mirror_ and _Packs_ (collectively known as the _Interface_) configuration from the _data/conf/self/senses.yaml_ file.

        :return: _Interface_ specific configurations.
        :rtype: dict

        """
        # TODO: mismatch between senses and interface naming scheme...
        if not self.sense_conf:
            self.sense_conf = self._self_configuration('senses')
        return self.sense_conf


    def load_avatar_configuration(
        self
    ) -> munch.Munch:
        if len(self.avatar_conf) == 0:
            self.avatar_conf = self._self_configuration('avatars')
        return self.avatar_conf


    def load_apparel_configuration(
        self
    ) -> munch.Munch:
        """_summary_

        :return: _description_
        :rtype: dict
        """
        # TODO: separate sheet conf from state conf.
        #       used in repo to load in assets
        #       used again in world for state information
        if len(self.apparel_conf) == 0:
            self.apparel_conf = self._self_configuration('apparel')
        return self.apparel_conf


    def load_composite_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Composite_ configuration from the _data/conf/forms/composite.yaml_.file.

        :return: _Composite_ specific configurations
        :rtype: dict
        """
        if len(self.composite_conf) == 0:
            self.composite_conf = self._form_configuration('composite')
        return self.composite_conf


    def load_tile_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Tile_ configuration from the _data/conf/forms/tiles.yaml_ file

        :return: _Tile_ specific configurations
        :rtype: dict
        """

        if len(self.tile_sheet_conf) == 0:
            self.tile_sheet_conf = self._form_configuration('tiles')
        return self.tile_sheet_conf


    def load_sprite_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Sprite_ configuration from the _data/conf/entities/sprites.yaml_ file.

        :return: _Sprite_ specific configurations parsed into `(sprite_stature_conf, sprite_property_conf, sprite_sheet_conf, sprite_dimensions)`-tuple
        :rtype: tuple

        .. note:
            The _Sprite_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class uses the property and state information to manage _Sprite_ states. The `onta.loader.repo.Repo` class uses the state and sheet information to load the spritesheets into memory.
        """    
        if len(self.sprite_stature_conf) == 0 or \
            len(self.sprite_property_conf) == 0 or \
            len(self.sprite_sheet_conf) == 0 or \
            not self.sprite_size:

            sprites_conf = self._entity_configuration('sprites')

            self.sprite_stature_conf = sprites_conf.stature
            self.sprite_size = sprites_conf.size

            for sprite_key, sprite_conf in sprites_conf.sprites.items():
                setattr(self.sprite_property_conf, sprite_key, sprite_conf.properties)
                setattr(self.sprite_sheet_conf, sprite_key, sprite_conf.sheets)

    
        return (
            self.sprite_stature_conf, 
            self.sprite_property_conf, 
            self.sprite_sheet_conf, 
            ( self.sprite_size.w, self.sprite_size.h)
        )


    def load_strut_configuration(
        self
    ) -> tuple:
        """Returns the parsed _Strut_ configuration from the _data/conf/forms/struts.yaml_ file.

        :return: _Strut_ specific configurations parsed into `(strut_property_conf, strut_sheet_conf)`-tuple.
        :rtype: tuple

        .. note::
            The _Strut_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class use the property information to determine how _Strut_\s react to _Sprite_ states. The `onta.loader.repo.Repo` class uses the sheet infromation to load the strutsheet into memory.
        .. note::
            Both `onta.world.World` and `onta.loader.repo.Repo` require the dimensions of a _Strut_, e.g. its (_w_, _h_) tuple, for calculations. Rather than dispensing with the separation between sheet and property configuration, this value is added to both configuration dictionary. A little bit of redundancy can be a good thing...
        """
        if not self.strut_property_conf or not self.strut_sheet_conf:
            struts_conf = self._form_configuration('struts')

            for strut_key, strut in struts_conf.items():
                setattr(self.strut_property_conf, strut_key, strut.properties)
                setattr(self.strut_property_conf.get(strut_key), 'size', strut.size) 
                setattr(
                    self.strut_sheet_conf,
                    strut_key,
                    munch.munchify({
                        key: val for key, val in strut.items()
                        if key != 'properties'
                    })
                )

        return ( self.strut_property_conf, self.strut_sheet_conf )


    def load_plate_configuration(
        self
    ) -> tuple:
        """Returns the parsed _Plate_ configuration from the _data/conf/forms/plate.yaml_ file. 

        :return: _Plate_ specific configurations parsed into `(plate_property_conf, strut_sheet_conf)`-tupe.
        :rtype: tuple

        .. note::
            - Size is _both_ a game property and an image configuration property.
        """
        if not self.plate_property_conf or not self.plate_sheet_conf:

            plates_conf = self._form_configuration('plates')

            for plate_key, plate_conf in plates_conf.items():
                setattr(self.plate_property_conf, plate_key, plate_conf.properties)
                setattr(self.plate_property_conf.get(plate_key), 'size', plate_conf.size)
                setattr(
                    self.plate_sheet_conf,
                    plate_key, 
                    munch.munchify({
                        key: val for key, val in plate_conf.items()
                        if key != 'properties'
                    })
                )
        
        return ( self.plate_property_conf, self.plate_sheet_conf )