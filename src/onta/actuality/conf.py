import os
from typing import Union
import yaml
import munch

from onta.metaphysics \
    import settings, constants

class Conf():
    """
    Configuration is wrapped in the `onta.actuality.conf.Conf` class so a custom _ontology_ at a different location than the default location can be passed into the engine. This object can be a constructed with a path to that _ontology_ to override the preloaded configuration sets.
    """


    def __init__(
        self, 
        data_dir = settings.DEFAULT_DIR
    ) -> None:
        """
        Initializes a `onta.actuality.conf.Conf` object with the user provided _ontology_ path. If not path is provided, the path defaults to `onta.metaphysics.settings.DEFAULT_DIR`, i.e. the installation's tutorial _ontology_.
        """
        self.conf_dir = os.path.join(
            data_dir, 
            *settings.CONF_PATH
        )
        self._init_fields()
    

    def _init_fields(
        self
    ) -> None:
        self.sprite_size = munch.Munch({})
        self.sprite_stature_conf = munch.Munch({})
        self.sprite_property_conf = munch.Munch({})
        self.sprite_sheet_conf = munch.Munch({})
        self.strut_property_conf = munch.Munch({})
        self.strut_sheet_conf = munch.Munch({})
        self.plate_property_conf = munch.Munch({})
        self.plate_sheet_conf = munch.Munch({})
        self.tile_sheet_conf = munch.Munch({})
        self.projectile_property_conf = munch.Munch({})
        self.projectile_img_conf = munch.Munch({})
        self.will_conf = munch.Munch({})
        self.qualia_conf = munch.Munch({})
        self.avatar_conf = munch.Munch({})
        self.expression_conf = munch.Munch({})
        self.composite_conf = munch.Munch({})
        self.apparel_conf = munch.Munch({})

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
        :rtype: munch.Munch
        """
        conf_path = os.path.join(
            self.conf_dir, 
            group_key, 
            f'{type_key}.yaml'
        )
        with open(
            conf_path, 
            'r'
        ) as infile:
            conf = munch.munchify(
                yaml.safe_load(infile)
            )
        return conf

    def _self_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/self_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Self_ configuration formatted into dictionary.
        :rtype: munch.Munch
        """
        return self.__configuration(
            type_key, 
            constants.OntaTypes.SELF.value
        )

    def _form_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/forms_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Form_ configuration formatted into dictionary
        :rtype: munch.Munch
        """
        return self.__configuration(
            type_key, 
            constants.OntaTypes.FORM.value
        )

    def _entity_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/entities_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Entity_ configuration formatted into dictionary.
        :rtype: munch.Munch
        """
        return self.__configuration(
            type_key, 
            constants.OntaTypes.ENTITY.value
        )


    def _dialectic_configuration(
        self, 
        type_key: str
    ) -> munch.Munch:
        """Returns a specific type of configuration from the _data/conf/dialectics_ directory.

        :param type_key: Key for the type of configuration being retrieved.
        :type type_key: str
        :return: _Dialectic_ configuration formatted into dictionary.
        :rtype: munch.Munch
        """
        return self.__configuration(
            type_key, 
            constants.OntaTypes.DIALECTICS.value
        )


    ## SELF CONFIGURATION


    def load_will_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Will_ configuration from the _data/conf/self/will.yaml_ file.

        :return: _Control_ configuration.
        :rtype: munch.Munch
        """
        if len(self.will_conf) == 0:
            self.will_conf = self._self_configuration(
                constants.SelfTypes.WILL.value
            )
        return self.will_conf

    
    def load_qualia_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Slot_, _Mirror_ and _Packs_ (collectively known as the _Interface_) configuration from the _data/conf/self/qualia.yaml_ file.

        :return: _Sense_ configurations.
        :rtype: munch.Munch
        """
        # TODO: mismatch between qualia and interface naming scheme...
        if not self.qualia_conf:
            self.qualia_conf = self._self_configuration(
                constants.SelfTypes.QUALIA.value
            )
        return self.qualia_conf


    def load_avatar_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Avatar_ configuration from the _data/conf/self/avatars.yaml_ file.

        :return: _Avatar_ configuration.
        :rtype: munch.Munch
        """
        if len(self.avatar_conf) == 0:
            self.avatar_conf = self._self_configuration(
                constants.SelfTypes.AVATAR.value
            )
        return self.avatar_conf


    def load_self_configuration(
        self,
        self_type
    ) -> Union[
        munch.Munch,
        None
    ]:
        # NOTE: generalized method that routes through cache
        if self_type == constants.SelfTypes.QUALIA.value:
            return self.load_qualia_configuration()
        if self_type == constants.SelfTypes.AVATAR.value:
            return self.load_avatar_configuration()
        if self_type == constants.SelfTypes.WILL.value:
            return self.load_will_configuration()
        return None


    ## DIALECTIC CONFIGURATION


    def load_expression_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Expression_ configuration from the _data/conf/dialectics/expression.yaml_ file.

        :return: _Expression_ configuration.
        :rtype: munch.Munch
        """
        if len(self.expression_conf) == 0:
            self.expression_conf = self._dialectic_configuration(
                constants.DialecticType.EXPRESSION.value
            )
        # NOTE: Expressions do not have properties, so to make return type consistent
        #       across dialectics, return None for expression properties
        return (
            None,
            self.expression_conf
        )


    def load_projectile_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Projectile_ configuration from the _data/conf/dialectics/projectile.yaml_ file.

        :return: _Projectile_ configuration.
        :rtype: munch.Munch
        """
        if len(self.projectile_property_conf) == 0 or \
            len(self.projectile_img_conf) == 0:
            projectiles_conf = self._dialectic_configuration(
                constants.DialecticType.PROJECTILE.value
            )

            # NOTE: separate in-game configuration from image configuration
            for project_key, projectile_conf in projectiles_conf.items():
                setattr(
                    self.projectile_property_conf, 
                    project_key, 
                    projectile_conf.properties
                )
                setattr(
                    self.projectile_property_conf.get(project_key),
                    'size',
                    projectile_conf.size
                )
                setattr(
                    self.projectile_img_conf,
                    project_key,
                    munch.munchify({
                        key: value 
                        for key, value 
                        in projectile_conf.items()
                        if key != 'properties'
                    })
                )
        return (
            self.projectile_property_conf, 
            self.projectile_img_conf
        )


    def load_dialectic_configuration(
        self,
        dialectic_type
    ) -> Union[
        munch.Munch,
        None
    ]:
        # NOTE: generalized method that routes through cache
        if dialectic_type == constants.DialecticType.PROJECTILE.value:
            return self.load_projectile_configuration()
        if dialectic_type == constants.DialecticType.EXPRESSION.value:
            return self.load_expression_configuration()
        return None


    ## ENTITY CONFIGURATION


    def load_apparel_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Apparel_ configuration from the _data/conf/entity/apparel.yaml_ file.

        :return: _Apparel_ configuration.
        :rtype: munch.Munch
        """
        # TODO: separate sheet conf from state conf.
        #       used in repo to load in assets
        #       used again in world for state information
        if len(self.apparel_conf) == 0:
            self.apparel_conf = self._entity_configuration(
                constants.EntityType.APPAREL.value
            )
        return self.apparel_conf


    def load_sprite_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Sprite_ configuration from the _data/conf/entity/sprite.yaml_ file.

        :return: _Sprite_ specific configurations parsed into `(sprite_stature_conf, sprite_property_conf, sprite_sheet_conf, sprite_dimensions)`-tuple
        :rtype: tuple

        .. note:
            The _Sprite_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class uses the property and state information to manage _Sprite_ states. The `onta.loader.repo.Repo` class uses the state and sheet information to load the spritesheets into memory.
        """    
        if len(self.sprite_stature_conf) == 0 or \
            len(self.sprite_property_conf) == 0 or \
            len(self.sprite_sheet_conf) == 0 or \
            not self.sprite_size:

            sprites_conf = self._entity_configuration(
                constants.EntityType.SPRITE.value
            )

            self.sprite_stature_conf = sprites_conf.stature
            self.sprite_size = sprites_conf.size

            for sprite_key, sprite_conf in sprites_conf.sprites.items():
                setattr(
                    self.sprite_property_conf, 
                    sprite_key, 
                    sprite_conf.properties
                )
                setattr(
                    self.sprite_sheet_conf, 
                    sprite_key, 
                    sprite_conf.sheets
                )

        return (
            self.sprite_stature_conf, 
            self.sprite_property_conf, 
            self.sprite_sheet_conf, 
            ( 
                self.sprite_size.w, 
                self.sprite_size.h
            )
        )

    
    def load_entity_configuration(
        self,
        entity_type
    ) -> Union[
        munch.Munch,
        None
    ]:
        # NOTE: generalized method that routes through cache
        if entity_type == constants.EntityType.SPRITE.value:
            return self.load_sprite_configuration()
        if entity_type == constants.EntityType.APPAREL.value:
            return self.load_apparel_configuration()


    ## FORM CONFIGURATION

    def load_composite_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Composite_ configuration from the _data/conf/form/composite.yaml_.file.

        :return: _Composite_ configuration
        :rtype: munch.Munch
        """
        if len(self.composite_conf) == 0:
            self.composite_conf = self._form_configuration(
                constants.FormType.COMPOSITE.value
            )
        # NOTE: Compositions do not have properties, so to make return type consistent
        #       across forms, return None for composition properties
        return (
            None,
            self.composite_conf
        )


    def load_tile_configuration(
        self
    ) -> munch.Munch:
        """Returns the parsed _Tile_ configuration from the _data/conf/form/tile.yaml_ file

        :return: _Tile_ configuration
        :rtype: munch.Munch
        """

        if len(self.tile_sheet_conf) == 0:
            self.tile_sheet_conf = self._form_configuration(
                constants.FormType.TILE.value
            )

        # NOTE: Tiles do not have properties, so to make return type consistent
        #       across forms, return None for tile properties
        return (
            None,
            self.tile_sheet_conf
        )


    def load_strut_configuration(
        self
    ) -> tuple:
        """Returns the parsed _Strut_ configuration from the _data/conf/form/strut.yaml_ file.

        :return: _Strut_ specific configurations parsed into `(strut_property_conf, strut_sheet_conf)`-tuple.
        :rtype: tuple

        .. note::
            The _Strut_ configuration is split into the different sections used by different components of the engine, so that irrelevant information isn't passed to components that do not require it. The `onta.world.World` class use the property information to determine how _Strut_\s react to _Sprite_ states. The `onta.loader.repo.Repo` class uses the sheet infromation to load the strutsheet into memory.
        .. note::
            Both `onta.world.World` and `onta.loader.repo.Repo` require the dimensions of a _Strut_, e.g. its (_w_, _h_) tuple, for calculations. Rather than dispensing with the separation between sheet and property configuration, this value is added to both configuration dictionary. A little bit of redundancy can be a good thing...
        """
        if not self.strut_property_conf or \
            not self.strut_sheet_conf:
            struts_conf = self._form_configuration(
                constants.FormType.STRUT.value
            )

            for strut_key, strut in struts_conf.items():
                setattr(
                    self.strut_property_conf, 
                    strut_key, 
                    strut.properties
                )
                setattr(
                    self.strut_property_conf.get(strut_key), 
                    'size',
                    strut.size
                ) 
                setattr(
                    self.strut_sheet_conf,
                    strut_key,
                    munch.munchify({
                        key: val 
                        for key, val 
                        in strut.items()
                        if key != 'properties'
                    })
                )

        return ( 
            self.strut_property_conf, 
            self.strut_sheet_conf 
        )


    def load_plate_configuration(
        self
    ) -> tuple:
        """Returns the parsed _Plate_ configuration from the _data/conf/form/plate.yaml_ file. 

        :return: _Plate_ specific configurations parsed into `(plate_property_conf, strut_sheet_conf)`-tupe.
        :rtype: tuple

        .. note::
            - Size is _both_ a game property and an image configuration property.
        """
        if not self.plate_property_conf or \
            not self.plate_sheet_conf:

            plates_conf = self._form_configuration(
                constants.FormType.PLATE.value
            )

            for plate_key, plate_conf in plates_conf.items():
                setattr(
                    self.plate_property_conf, 
                    plate_key, 
                    plate_conf.properties
                )
                setattr(
                    self.plate_property_conf.get(plate_key), 
                    'size', 
                    plate_conf.size
                )
                setattr(
                    self.plate_sheet_conf,
                    plate_key, 
                    munch.munchify({
                        key: val 
                        for key, val 
                        in plate_conf.items()
                        if key != 'properties'
                    })
                )
        
        return ( 
            self.plate_property_conf, 
            self.plate_sheet_conf 
        )


    def load_form_configuration(
        self,
        form_type
    ) -> Union[
        munch.Munch,
        None
    ]:
        # NOTE: generalized method that routes through cache...
        if form_type == constants.FormType.PLATE.value:
            return self.load_plate_configuration()

        if form_type == constants.FormType.TILE.value:
            return self.load_tile_configuration()

        if form_type == constants.FormType.STRUT.value:
            return self.load_strut_configuration()

        if form_type == constants.FormType.COMPOSITE.value:
            return self.load_composite_configuration()

        return None