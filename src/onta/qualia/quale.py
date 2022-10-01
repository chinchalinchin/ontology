from onta.actuality import conf
from onta.metaphysics import device, settings
from onta.qualia import apriori


class Quale():
    
    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        self._init_conf(
            config, 
            player_device
        )


    def _init_conf(
        self, 
        config: conf.Conf,
        player_device: device.Device
    ) -> None:
        """_summary_

        :param config: _description_
        :type config: conf.Conf

        .. note::
            ```python
            self.quale_conf = {
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
            ```
        """
        configure = config.load_qualia_configuration()

        self.quale_conf = configure.qualia
        self.thought_conf = configure.thoughts
        self.sizes = configure.apriori.sizes
        self.breakpoints = apriori.format_breakpoints(
            configure.apriori.breakpoints
        )    
        self.media_size = apriori.find_media_size(
            player_device.dimensions, 
            self.sizes, 
            self.breakpoints
        )
        self.properties = configure.apriori.properties
        self.styles = configure.apriori.styles.get(self.media_size)
        self.transparency = configure.apriori.transparency
        self.theme = configure.apriori.theme
        self.avatar_conf = config.load_avatar_configuration()

