from math import trunc, log10, floor
import functools
from frozendict import frozendict
import numba

import time

from typing import Dict, List, Tuple


def freezeargs(func):
    """Transform mutable dictionnary
    Into immutable
    Useful to be compatible with cache

    .. todo::
        need to recurse
    """

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple(
            [   
                frozendict(arg) 
                if isinstance(arg, dict) 
                else tuple(arg) 
                if isinstance(arg, list)
                else arg
                for arg in args
            ]
        )
        kwargs = {
            k: frozendict(v) 
            if isinstance(v, dict)
            else v 
            for k, v in kwargs.items()
        }
        return func(*args, **kwargs)
    return wrapped


def current_ms_time():
    return round(time.time() * 1000)


@numba.jit(nopython=True, nogil=True, parallel=True)
def truncate(number: float, digits: int) -> float:
    stepper = 10.0 ** digits
    return trunc(stepper * number) / stepper


@numba.jit(nopython=True, nogil=True, parallel=True)
def strip_string_array(array: List[str]) -> List[str]:
    new_array = []
    for string in array:
        new_array.append(string.strip())
    return new_array


@numba.jit(nopython=True, nogil=True, parallel=True)
def split_and_strip(string: str, upper: bool = True, delimiter=",") -> List[str]:
    if upper:
        return strip_string_array(string.upper().split(delimiter))
    return strip_string_array(string.lower().split(delimiter))


@numba.jit(nopython=True, nogil=True, parallel=True)
def reorder_dict(this_dict: Dict[str, str], desired_order: List[str]):
    ordered_keys = [
        order for order in desired_order if order in list(this_dict.keys())]
    return {order: this_dict[order] for order in ordered_keys}


@numba.jit(nopython=True, nogil=True, parallel=True)
def round_array(array: List[float], decimals: int) -> List[float]:
    return [round(element, decimals) for element in array]


@numba.jit(nopython=True, nogil=True, parallel=True)
def intersect_dict_keys(dict1: dict, dict2: dict) -> Tuple[dict, dict]:
    """
    Generates two new dictionaries from the inputted dictionaries such that the new dictionaries contain the same keys. In other words, this function takes the intersection of the dictionary keys and generates two new dictionaries with *only* those keys.
    """
    return {
        x: dict1[x] 
        for x in dict1.keys() 
        if x in dict2.keys()
    }, {
        x: dict2[x] 
        for x in dict2.keys() 
        if x in dict1.keys()
    }


@numba.jit(nopython=True, nogil=True, parallel=True)
def complement_dict_keys(dict1: dict, dict2: dict) -> dict:
    """
    Returns the transformed dictionaries whose keys are a complement relative to the second dictionary keys. In other words, this function takes the complement of the first dictionary keys relative to the second dictionary keys and visa versa,
    """
    return {
        x: dict1[x] for x 
        in dict1.keys() if x not in dict2.keys()
    }, {
        x: dict2[x] for x 
        in dict2.keys() if x not in dict1.keys()
    }


@numba.jit(nopython=True, nogil=True, parallel=True)
def significant_digits(number: float, digits: int) -> float:
    return number if number == 0 \
        else round(number, -int(floor(log10(abs(number)))) + (digits - 1))


@numba.jit(nopython=True, nogil=True, parallel=True)
def get_first_json_key(this_json: dict) -> str:
    return list(this_json.keys())[0]