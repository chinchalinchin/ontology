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

@pytest.mark.parametrize('proj_key,proj_dir,proj_dim',[
    ( 'arrow', 'left', (41,10) ),
    ( 'arrow', 'right', (41, 10) ),
    ( 'arrow', 'up', (41, 10) ),
    ( 'arrow', 'down', (41, 10) )
])
def test_get_projectile_frame(
    repository,
    proj_key,
    proj_dir,
    proj_dim
):
    proj_frame = repository.get_projectile_frame(proj_key, proj_dir)
    assert isinstance(proj_frame, Image.Image)
    if proj_key in [ 'left', 'right' ]:
        assert proj_frame.size == proj_dim
    if proj_key in ['up', 'down']:
        assert proj_frame.size == (proj_dim[1], proj_dim[0])

    