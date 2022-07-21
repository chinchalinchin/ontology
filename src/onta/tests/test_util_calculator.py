import pytest

import onta.util.calculator as calculator

@pytest.mark.parametrize('rect_a,rect_b,intersects',[
    ((), (),True),
    ((), (), False),
    ((), (), True),
    ((), (), False),
    ((), (),True),
    ((), (), False),
    ((), (), True),
    ((), (), False),
])
def test_intersection(rect_a, rect_b, intersects):
    assert calculator.intersection(rect_a, rect_b, intersects)
