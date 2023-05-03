import copy

from pyanimate.shape import Shape


def test_add() -> None:
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 + s2 == Shape(4, 6)


def test_sub() -> None:
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 - s2 == Shape(-2, -2)


def test_mul() -> None:
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 * s2 == Shape(3, 8)


def test_truediv() -> None:
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s2 / s1 == Shape(3 / 1, 4 / 2)


def test_floordiv() -> None:
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s2 // s1 == Shape(3 // 1, 4 // 2)


def test_mod() -> None:
    s1 = Shape(2, 2)
    s2 = Shape(3, 4)
    assert s2 % s1 == Shape(1, 0)


def test_deepcopy() -> None:
    s1 = Shape(2, 2)
    s2 = copy.deepcopy(s1)
    assert s1 == s2
    assert s1 is not s2
