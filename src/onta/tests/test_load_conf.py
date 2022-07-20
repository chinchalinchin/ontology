from ..load import conf

import pytest


@pytest.mark.parametrize('obj,el,keys',[
    ('hero', 'hero', ['initial', 'dimensions', 'sheets', 'states']),
    ('struts', 'apartment_wall', ['image', 'properties']),
    ('struts', 'apartment_roof', ['image', 'properties']),
    ('struts', 'apartment_steps', ['image', 'properties']),
    ('struts', 'apartment_door', ['image', 'properties']),
    ('struts', 'apartment_chimney', ['image', 'properties']),
    ('tiles', 'coal', ['image']),
    ('tiles', 'grass', ['image']),
    ('tiles', 'mud', ['image']),
    ('tiles', 'lava', ['image']),
    ('tiles', 'sand', ['image']),
])
def test_configuration(obj, el, keys):
    config = conf.configuration(obj)
    assert config.get(el) is not None
    assert all(key in keys for key in list(config[el].keys()))