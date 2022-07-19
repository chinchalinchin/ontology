from ..loader import parser

HERO_KEYS = ['initial', 'dimensions', 'sheets', 'states']

def test_hero_configuration():
    conf = parser.hero_configuration()
    conf_keys = list(conf['entity'].keys())
    assert conf.get('entity') is not None
    assert all(key in HERO_KEYS for key in conf_keys)