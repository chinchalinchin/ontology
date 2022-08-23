import pytest

from PIL import Image
import os 

from onta.loader.repo import Repo

@pytest.fixture
def directory():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    data_dir = os.path.join(project_dir, 'src', 'data')
    return data_dir

@pytest.fixture
def repository(directory):
    return Repo(directory)

@pytest.mark.parametrize('proj_key,proj_def,proj_dir,proj_dim',[
    ( 'arrow', 'left', 'left', ( 41, 10 ) ),
    ( 'arrow', 'left', 'right', ( 41, 10 ) ),
    ( 'arrow', 'left',  'up', ( 41, 10 ) ),
    ( 'arrow', 'left', 'down', ( 41, 10 ) )
])
def test_get_projectile_frame(
    repository,
    proj_key,
    proj_def,
    proj_dir,
    proj_dim
):
    proj_frame = repository.get_projectile_frame(proj_key, proj_dir)
    assert isinstance(proj_frame, Image.Image)

    # assert image is rotated according to its definition
    if proj_def in ['left', 'right']:
        if proj_dir in [ 'left', 'right' ]:
            assert proj_frame.size == proj_dim
        else:
            assert proj_frame.size == (proj_dim[1], proj_dim[0])
    else:
        if proj_dir in [ 'up', 'down' ]:
            assert proj_frame.size == proj_dim
        else:
            assert proj_frame.size == (proj_dim[1], proj_dim[0])


@pytest.mark.parametrize('express_key,express_dim',
[
    ('anger', ( 16, 16 ) ),
    ('confusion', ( 16, 16 ) ),
    ('joy', ( 16, 16 ) ),
    ('sadness', ( 16, 16 ) ),
    ('surprise', ( 16, 16 ) ),
    ('love', ( 9, 8 ) ),
    ('hate', ( 15, 16 ) ),
    ('help', ( 16, 16 ) )
])
def test_get_expression_frame(
    repository,
    express_key,
    express_dim
):
    express_frame = repository.get_expression_frame(express_key)
    assert isinstance(express_frame, Image.Image)
    assert express_frame.size == express_dim