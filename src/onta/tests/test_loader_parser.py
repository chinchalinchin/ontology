from ..loader import parser

import pytest


@pytest.mark.parametrize('obj,el,keys',[
    ('hero', 'hero', ['initial', 'dimensions', 'sheets', 'states']),
    ('tiles', 'apartment_wall', ['image', 'properties']),
    ('tiles', 'apartment_roof', ['image', 'properties']),
    ('tiles', 'apartment_steps', ['image', 'properties']),
    ('tiles', 'apartment_door', ['image', 'properties']),
    ('tiles', 'apartment_chimney', ['image', 'properties']),
])
def test_configuration(obj, el, keys):
    conf = parser.configuration(obj)
    assert conf.get(el) is not None
    assert all(key in keys for key in list(conf[el].keys()))