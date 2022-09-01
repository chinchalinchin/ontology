from typing import Union
import munch

import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.loader.conf as conf
import onta.loader.state as state
import onta.util.logger as logger
import onta.engine.qualia.apriori as apriori
import onta.engine.qualia.thoughts.bauble as bauble
import onta.engine.qualia.thoughts.symbol as symbol

import onta.engine.facticity.formulae as formulae

log = logger.Logger('onta.engine.qualia.menu', settings.LOG_LEVEL)

BAUBLE_THOUGHTS = [ 'armory', 'equipment', 'inventory' ]
SYMBOL_THOUGHTS = [ 'map', 'status' ]

class NoeticQuale():
    """
    
    A `NoeticQuale` is essentially an in-game menu; it composed of "ideas", i.e. buttons, the player iterates throguh and then executes. These "ideas" become "thoughts", i.e. submenus, when executed. When an "idea" is executed, focus is shifted to the "thought" until the player pops back into the "idea" selection menu.
    """

    menu_conf = munch.Munch({})
    """
    self.menu_conf = {
        'media_size_1': {
            'idea': {
                # ...
            },
            'bauble': {
                # ...
            },
            'aside': {
                # ...
            },
            'focus' : {
                # ...
            }
        },
        # ...
    }
    """
    thoughts = munch.Munch({})
    """
    self.thoughts = {
        'thought_1': {
            # ...
        },
        # ...
    }
    """
    ideas = munch.Munch({})
    """
    self.ideas = {
        'thought_1': {
            'left': 'enabled',
            'middle': 'enabled',
            'right': 'enabled'
        },
        # ...
    }
    """
    idea_rendering_points = []
    idea_frame_map = []
    idea_piece_map = []
    active_idea = None
    active_thought = None
    avatar_conf = munch.Munch({})
    properties = munch.Munch({})
    styles = munch.Munch({})
    theme = munch.Munch({})
    sizes = []
    breakpoints = []
    menu_activated = False
    media_size = None
    alpha = None

    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_conf(config)
        self.media_size = apriori.find_media_size(
            player_device.dimensions, 
            self.sizes, 
            self.breakpoints
        )
        self._init_idea_positions(player_device)
        self._init_thoughts(
            player_device,
            state_ao
        )
        self._init_ideas(state_ao)


    def _init_conf(
        self, 
        config: conf.Conf
    ) -> None:
        configure = config.load_qualia_configuration()
        self.menu_conf = configure.menu
        self.sizes = configure.sizes
        self.styles = configure.styles
        self.properties = configure.properties.menu
        self.alpha = configure.transparency
        self.theme = apriori.construct_themes(
            configure.theme
        )
        self.breakpoints = apriori.format_breakpoints(
            configure.breakpoints
        )
        self.avatar_conf = config.load_avatar_configuration().avatars



    def _init_idea_positions(
        self, 
        player_device: device.Device
    ) -> None:
        menu_margins = (
            self.styles.get(self.media_size).menu.margins.w,
            self.styles.get(self.media_size).menu.margins.h
        )
        menu_padding = (
            self.styles.get(self.media_size).menu.padding.w,
            self.styles.get(self.media_size).menu.padding.h
        )
        menu_stack = self.styles.get(self.media_size).menu.stack
        # all idea component pieces have the same dim, so any will do...
        idea_conf = self.menu_conf.get(self.media_size).idea.enabled

        # NOTE: ideas are "thought" buttons
        # [ (left_w, left_h), (middle_w, middle_h), (right_w, right_h) ]
        dims = [
            ( idea_conf.get(piece).size.w, idea_conf.get(piece).size.h ) 
            for piece in self.properties.ideas.pieces
        ]

        self.idea_rendering_points = formulae.idea_coordinates(
            dims,
            len(self.properties.thoughts),
            len(idea_conf),
            player_device.dimensions,
            menu_stack,
            menu_margins,
            menu_padding
        )


    def _init_thoughts(
        self,
        player_device: device.Device,
        state_ao: state.State
    ):
        # need statuses, pieces and sizes from the following confs
        # in order to initialize a Tab
        components_conf = munch.Munch({
            'bauble': self.menu_conf.get(self.media_size).bauble,
            'focus': self.menu_conf.get(self.media_size).focus,
            'aside': self.menu_conf.get(self.media_size).aside,
            'concept': self.menu_conf.get(self.media_size).concept,
            'conception': self.menu_conf.get(self.media_size).conception
        })

        # all button component pieces have the same pieces, so any will do...
        idea_conf = self.menu_conf.get(self.media_size).idea.enabled
        full_width = sum(
            idea_conf.get(piece).size.w 
            for piece in self.properties.ideas.pieces
        )
        full_height = idea_conf.get(
            self.properties.ideas.pieces[0]
        ).size.h
        idea_dim = (full_width, full_height)

        menu_styles = self.styles.get(self.media_size).menu

        for thought_key, thought_conf in self.properties.thoughts.items():
            log.debug(f'Creating {thought_key} thought...', 'Menu._init_tabs')
            
            if thought_key in BAUBLE_THOUGHTS:
                # TODO:? There is a redundancy here. the class itself knows which thoughts are baubles
                # through this constant, but the configuration data structure also passes in that information. 

                # this brings up the question. how much of the data should be in the configuration and how much
                # should be programmatic logic?

                setattr(
                    self.thoughts, 
                    thought_key,
                    bauble.BaubleThought(
                        thought_key,
                        thought_conf,
                        components_conf,
                        menu_styles,
                        self.avatar_conf,
                        self.idea_rendering_points[0],
                        idea_dim,
                        player_device.dimensions,
                        state_ao,
                    )
                )
            elif thought_key in SYMBOL_THOUGHTS:
                pass
                # TODO: this


    def _init_ideas(
        self, 
        state_ao: state.State
    ) -> None:
        """_summary_

        :param state_ao: _description_
        :type state_ao: state.State
        """
        # TODO: calculate based on state information

        # NOTE: this is what creates `self.thoughts`
        #       `self.thoughts`
        for i, name in enumerate(list(self.properties.thoughts.keys())):
            if i == 0:
                self._activate_idea(name)
                self.active_idea = i
            else:
                self._enable_idea(name)


    def _activate_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: 'active' for piece in self.properties.ideas.pieces
            })
        )


    def _disable_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: 'disabled' for piece in self.properties.ideas.pieces
            })
        )


    def _enable_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: 'enabled' for piece in self.properties.ideas.pieces
            })
        )


    def _increment_idea(
        self
    ) -> None:
        """_summary_
        """
        idea_list = list(self.thoughts.keys())
        ## TODO: skip disabled idea buttons
        previous_active = self.active_idea
        self.active_idea -= 1

        if self.active_idea < 0:
            self.active_idea = len(idea_list) - 1
        
        self._enable_idea(idea_list[previous_active])
        self._activate_idea(idea_list[self.active_idea])


    def _decrement_idea(
        self
    ) -> None:
        """_summary_
        """
        idea_list = list(self.thoughts.keys())
        ## TODO: skip disabled buttons
        previous_active = self.active_idea
        self.active_idea += 1

        if self.active_idea > len(idea_list) - 1:
            self.active_idea = 0
        
        self._enable_idea(idea_list[previous_active])
        self._activate_idea(idea_list[self.active_idea])


    def _ideate(
        self,
    ) -> None:
        activate_thought_key = list(self.thoughts.keys())[self.active_idea]
        self.active_thought = self.thoughts.get(activate_thought_key)


    def _forget(
        self,
    ) -> None:
        self.active_thought = None


    def _calculate_idea_frame_map(
        self
    ) -> list:
        # NOTE **: frame changes ..
        self.idea_frame_map = [] 
        for piece_conf in self.ideas.values():
            for piece_state in piece_conf.values():
                self.idea_frame_map.append(piece_state)
        return self.idea_frame_map


    def _calculate_idea_piece_map(
        self
    ) -> list:
        # NOTE **: ...but pieces stay the same ...
        if not self.idea_piece_map:
            for piece_conf in self.ideas.values():
                for piece_key in piece_conf.keys():
                    self.idea_piece_map.append(piece_key)
        return self.idea_piece_map


    def _active_thought_key(
        self
    ) -> str:
        return list(self.thoughts.keys())[self.active_idea]


    def get_active_thought(
        self
    ) -> bauble.BaubleThought:
        # TODO: Union[bauble.BaubleThought, symbol.SymbolThought]
        return self.thoughts.get(
            self._active_thought_key()
        )


    def idea_maps(
        self
    ) -> tuple:
        return (
            self._calculate_idea_frame_map(), 
            self._calculate_idea_piece_map()
        )


    def toggle_menu(
        self
    ) -> None:
        self.menu_activated = not self.menu_activated


    def rendering_points(
        self, 
        interface_key: str
    ) -> list:
        if interface_key in [ 'idea', 'ideas' ]:
            return self.idea_rendering_points


    def update(
        self, 
        menu_input: Union[munch.Munch, None],
        game_world: world.World
    ) -> None:
        if menu_input:
            
            if menu_input.arise:
                self.toggle_menu()
                return

            # controls when traversing main button stack
            if self.active_thought is None:
                if menu_input.increment:
                    self._increment_idea()

                elif menu_input.decrement:
                    self._decrement_idea()

                elif menu_input.execute:
                    self._ideate()

                return

            if menu_input.reconsider:
                self._forget()
                return

            # controls when traversing tab stacks
            if isinstance(self.active_thought, bauble.BaubleThought):

                if menu_input.increment:
                    self.active_thought.increment_bauble_row()

                elif menu_input.decrement:
                    self.active_thought.decrement_bauble_row()

                elif menu_input.traverse:
                    self.active_thought.increment_bauble_selection()

                elif menu_input.reverse:
                    self.active_thought.decrement_bauble_selection()

                self.active_thought.update(game_world)

                return

            elif isinstance(self.active_thought, symbol.SymbolThought):
                pass