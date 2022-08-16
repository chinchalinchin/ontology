from math import trunc, log10, floor
import time

from typing import Dict, List


def current_ms_time():
    return round(time.time() * 1000)


def truncate(number: float, digits: int) -> float:
    stepper = 10.0 ** digits
    return trunc(stepper * number) / stepper


def reorder_dict(this_dict: Dict[str, str], desired_order: List[str]):
    ordered_keys = [
        order for order in desired_order 
        if order in list(this_dict.keys())
    ]
    return {order: this_dict[order] for order in ordered_keys}


def round_array(array: List[float], decimals: int) -> List[float]:
    return [round(element, decimals) for element in array]


def significant_digits(number: float, digits: int) -> float:
    return number if number == 0 \
        else round(number, -int(floor(log10(abs(number)))) + (digits - 1))
