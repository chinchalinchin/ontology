from math import trunc, log10, floor
import time

import numba

from typing import Dict, List


def current_ms_time():
    return round(time.time() * 1000)


@numba.jit(nopython=True, nogil=True, parallel=True)
def truncate(number: float, digits: int) -> float:
    stepper = 10.0 ** digits
    return trunc(stepper * number) / stepper


@numba.jit(nopython=True, nogil=True, parallel=True)
def reorder_dict(this_dict: Dict[str, str], desired_order: List[str]):
    ordered_keys = [
        order for order in desired_order 
        if order in list(this_dict.keys())
    ]
    return {order: this_dict[order] for order in ordered_keys}


@numba.jit(nopython=True, nogil=True, parallel=True)
def round_array(array: List[float], decimals: int) -> List[float]:
    return [round(element, decimals) for element in array]


@numba.jit(nopython=True, nogil=True, parallel=True)
def significant_digits(number: float, digits: int) -> float:
    return number if number == 0 \
        else round(number, -int(floor(log10(abs(number)))) + (digits - 1))


@numba.jit(nopython=True, nogil=True, fastmath=True)
def filter_nested_tuple(
    nested_tuple: tuple, 
    filter_value: str
) -> tuple:
    """_summary_

    :param nested_tuple: _description_
    :type nested_tuple: tuple
    :param filter_value: _description_
    :type filter_value: str
    :return: _description_
    :rtype: tuple

    .. note:: 
        Assumes the first element of the tuple is the index.
    """
    filtered = [
        tup
        for tup in iter(nested_tuple)
        if tup[0] == filter_value
    ]
    
    return filtered


def _init_jit():
    filter_nested_tuple(
        (('hello',123),('goodbye',123),),
        'hello'
    )

_init_jit()