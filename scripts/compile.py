import sys
import os

project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

sys.path.insert(0, os.path.join(project_path,'src'))

from onta.engine.static.calculator import cc_calculator
from onta.engine.static.formulae import cc_formulae
from onta.engine.static.paths import cc_paths

cc_calculator.compile()
cc_formulae.compile()
cc_paths.compile()

# why not work now?