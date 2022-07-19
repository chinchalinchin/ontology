import os
import yaml
import onta.settings as settings

def hero_configuration():
    hero_conf_path = os.path.join(settings.CONF_DIR, 'hero.yaml')
    with open(hero_conf_path, 'r') as infile:
        hero_conf = yaml.safe_load(infile)
    return hero_conf