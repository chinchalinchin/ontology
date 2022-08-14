# from setuptools import setup

# import sys
# import os

# script_path = os.path.dirname(os.path.realpath(__file__))

# sys.path.insert(0, os.path.join(script_path,'src'))

# from onta.engine.static.calculator import cc_calculator
# from onta.engine.static.formulae import cc_formulae
# from onta.engine.static.paths import cc_paths

# setup(
#     ext_modules=[
#         cc_calculator.distutils_extension(),
#         cc_formulae.distutils_extension(),
#         cc_paths.distutils_extension(),
#     ]
# )

# # setup(
# #     ext_modules=[
# #         Extension('cc_calculator', ['onta/engine/static/cc_calculator.cpython-38-x86_64-linux-gnu.so']),
# #         Extension('cc_formulae', ['onta/engine/static/cc_formulae.cpython-38-x86_64-linux-gnu.so']),
# #         Extension('cc_pats', ['onta/engine/static/cc_paths.cpython-38-x86_64-linux-gnu.so']),

# #     ]
# # )