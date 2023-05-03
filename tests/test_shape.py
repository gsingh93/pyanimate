import copy

from pyanimate.shape import Shape


def test_add():
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 + s2 == Shape(4, 6)


def test_sub():
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 - s2 == Shape(-2, -2)


def test_mul():
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s1 * s2 == Shape(3, 8)


def test_truediv():
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s2 / s1 == Shape(3 / 1, 4 / 2)


def test_floordiv():
    s1 = Shape(1, 2)
    s2 = Shape(3, 4)
    assert s2 // s1 == Shape(3 // 1, 4 // 2)


def test_mod():
    s1 = Shape(2, 2)
    s2 = Shape(3, 4)
    assert s2 % s1 == Shape(1, 0)


def test_deepcopy():
    s1 = Shape(2, 2)
    s2 = copy.deepcopy(s1)
    assert s1 == s2
    assert s1 is not s2
