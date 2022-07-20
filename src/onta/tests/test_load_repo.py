import onta.load.repo as repo

import pytest

from PIL import Image

TILE_WIDTH = 96
TILE_HEIGHT = 32
def test_init_tiles():
    repository = repo.Repo()
    assert isinstance(repository.tiles, dict)
    assert all(im.size[0] == TILE_WIDTH for im in repository.tiles.values())
    assert all(im.size[1] == TILE_HEIGHT for im in repository.tiles.values())