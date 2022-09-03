import munch


def find_media_size(
    device_dim: tuple, 
    sizes: list, 
    breakpoints: list
) -> str:
    """Iterate through ordered breakpoints and compare to screen dimensions until media size is found.

    :param player_device: Object representing the player device.
    :type player_device: device.Device
    :param sizes: List of sizes for the breakpoints, i.e. `len(sizes) == len(breakpoints) - 1`. So, if `sizes = ['small', 'large']` and `breakpoints = [(800,600)]`, then if the screen is (600,400), the size 'small' will be selected, where if screen is (900, 500) the size 'large' will be selected. 
    :type sizes: list
    :param breakpoints: List of tuples representing the points at which styles and layouts shift to accomodate a new screen sie.
    :type breakpoints: list
    :return: The name of the size within the breakpoint.
    :rtype: str
    """
    for i, break_point in enumerate(breakpoints):
        if device_dim[0] < break_point[0] and \
            device_dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]


def construct_themes(
    themes:munch.Munch
) -> None:
    """Convert nested RGBA map into tuple accessible through dot notation, `theme.theme_component`.

    :param themes: _description_
    :type themes: munch.Munch
    :return: _description_
    :rtype: _type_
    """
    theme = munch.Munch({})
    for theme_key, theme_map in themes.items():
        setattr(
            theme, 
            theme_key, 
            (
                theme_map.r, 
                theme_map.g, 
                theme_map.b, 
                theme_map.a
            )
        )
    return theme


def format_breakpoints(
    break_points: list
) -> list:
    """_summary_

    :param break_points: _description_
    :type break_points: list
    :return: _description_
    :rtype: list
    """
    return [
        (break_point.w, break_point.h) 
            for break_point in break_points
    ]

