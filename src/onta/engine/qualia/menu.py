from typing import Union
import munch

import onta.settings as settings
import onta.device as device
import onta.loader.conf as conf
import onta.loader.state as state
import onta.util.logger as logger
import onta.engine.qualia.display as display
import onta.engine.qualia.thought as thought

import onta.engine.facticity.formulae as formulae

log = logger.Logger('onta.engine.qualia.menu', settings.LOG_LEVEL)


class Menu():
    frame_maps = munch.Munch({})
    piece_maps = munch.Munch({})

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
    

    # TODO: what is tabs going to be???
    tabs = munch.Munch({})

    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_conf(config)
        self.media_size = formulae.find_media_size(
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
        self.theme = display.construct_themes(
            configure.theme
        )
        self.breakpoints = display.format_breakpoints(
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
        # all idea component pieces have the same pieces, so any will do...
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
            setattr(
                self.thoughts, 
                thought_key,
                thought.Thought(
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
        # NOTE **: frame changes ... 
        frame_map = []
        for piece_conf in self.ideas.values():
            for piece_state in piece_conf.values():
                frame_map.append(piece_state)
        setattr(self.frame_maps, 'idea', frame_map)
        return self.frame_maps.idea


    def _calculate_idea_piece_map(
        self
    ) -> list:
        # NOTE **: ...but pieces stay the same ...
        if not self.piece_maps.get('idea'):
            piece_map = []
            for piece_conf in self.ideas.values():
                for piece_key in piece_conf.keys():
                    piece_map.append(piece_key)
            setattr(self.piece_maps, 'idea', piece_map)
        return self.piece_maps.idea


    def _active_thought_key(
        self
    ) -> str:
        return list(self.thoughts.keys())[self.active_idea]


    def get_active_thought(
        self
    ) -> thought.Thought:
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
        menu_input: Union[munch.Munch, None]
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

            # controls when traversing tab stacks
            if menu_input.reverse:
                self._forget()
                return

            if self.active_thought.name == 'armory':
                pass
            if self.active_thought.name == 'equipment':
                pass
            if self.active_thought.name == 'inventory':
                pass
            if self.active_thought.name == 'map':
                pass