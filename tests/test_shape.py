import copy

import pytest
from kiwisolver import Variable

from pyanimate.shape import Shape


class TestShapeInt:
    def test_add(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 + s2 == Shape(4, 6)

    def test_sub(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 - s2 == Shape(-2, -2)

    def test_mul(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 * s2 == Shape(3, 8)

    # def test_truediv(self) -> None:
    #     s1 = Shape(1, 2)
    #     s2 = Shape(3, 4)
    #     assert s2 / s1 == Shape(3 / 1, 4 / 2)

    # def test_floordiv(self) -> None:
    #     s1 = Shape(1, 2)
    #     s2 = Shape(3, 4)
    #     assert s2 // s1 == Shape(3 // 1, 4 // 2)

    # def test_mod(self) -> None:
    #     s1 = Shape(2, 2)
    #     s2 = Shape(3, 4)
    #     assert s2 % s1 == Shape(1, 0)

    def test_deepcopy(self) -> None:
        s1 = Shape(2, 2)
        s2 = copy.deepcopy(s1)
        assert s1 == s2
        assert s1 is not s2

    def test_get(self) -> None:
        s1 = Shape(2, 3)
        s2 = s1.get()
        assert s1[0] == 2
        assert s1[1] == 3
        assert s2[0] == 2
        assert s2[1] == 3


class TestShapeVariableExpression:
    def test_get(self) -> None:
        x = Variable("x")
        e = x + 1
        s1 = Shape(x, e)
        s2 = s1.get()
        assert s1[0] is x
        assert s1[1] is e
        assert s2[0] == 0
        assert s2[1] == 1

    def test_get_mixed_int(self) -> None:
        x = Variable("x")
        s1 = Shape(x, 2)
        s2 = s1.get()
        assert s1[0] is x
        assert s1[1] == 2
        assert s2[0] == 0
        assert s2[1] == 2

    def test_get_mixed_float(self) -> None:
        x = Variable("x")
        s1 = Shape(2.0, x)
        s2 = s1.get()
        assert s1[0] == 2.0
        assert s1[1] is x
        assert s2[0] == 2.0
        assert s2[1] == 0

    def test_get_mixed_invalid(self) -> None:
        # TODO: Shape(1, 2.0) should also throw but doesn't
        s1 = Shape(2.0, 1)

        with pytest.raises(AssertionError):
            s1.get()
