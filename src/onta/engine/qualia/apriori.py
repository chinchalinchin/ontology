import munch


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

