import onta.load.repo as repo
import onta.tests.constants as constants
import pytest

def test_init_tiles():
    repository = repo.Repo()
    assert isinstance(repository.tiles, dict)
    assert all(im.size[0] == constants.TILE_WIDTH for im in repository.tiles.values())
    assert all(im.size[1] == constants.TILE_HEIGHT for im in repository.tiles.values())