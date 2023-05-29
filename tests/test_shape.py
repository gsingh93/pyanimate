import copy
import math

import pytest

from pyanimate.shape import Point, Shape
from pyanimate.solver import Expression, Term, Variable


class TestIntShape:
    def test_add(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 + s2 == s2 + s1 == Shape(4, 6)

    def test_sub(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 - s2 == Shape(-2, -2)

    def test_mul(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s1 * s2 == s2 * s1 == Shape(3, 8)

    def test_truediv(self) -> None:
        s1 = Shape(1, 2)
        s2 = Shape(3, 4)
        assert s2 / s1 == Shape(3 / 1, 4 / 2)

    def test_add_scalar(self) -> None:
        s = Shape(1, 2)
        assert s.add(2) == Shape(3, 4)

    def test_sub_scalar(self) -> None:
        s = Shape(1, 2)
        assert s.sub(2) == Shape(-1, 0)

    def test_mul_scalar(self) -> None:
        s = Shape(1, 2)
        assert s.mul(2) == Shape(2, 4)

    def test_truediv_scalar(self) -> None:
        s = Shape(1, 2)
        assert s.truediv(2) == Shape(0.5, 1)

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


class TestUnresolvedShape:
    @pytest.fixture
    def x(self) -> Variable:
        return Variable("x")

    @pytest.fixture
    def t(self, x: Variable) -> Term:
        return 2 * x

    @pytest.fixture
    def e(self, x: Variable, t: Term) -> Expression:
        return x + t + 1

    @pytest.fixture
    def s1(
        self, x: Variable, t: Term, e: Variable
    ) -> Shape[Variable | Term | Expression]:
        return Shape(x, t, e)

    def test_get_mixed_invalid(self) -> None:
        # TODO: Shape(1, 2.0) should also throw but doesn't
        s1 = Shape(2.0, 1)

        with pytest.raises(AssertionError):
            s1.get()

    def test_add(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(1, 2, 3)

        assert s1 + s2 == s2 + s1 == Shape(x + 1, t + 2, e + 3)

    def test_sub(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(1, 2, 3)

        assert s1 - s2 == -s2 - -s1 == Shape(x - 1, t - 2, e - 3)

    def test_mul(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(1, 2, 3)

        assert s1 * s2 == s2 * s1 == Shape(1 * x, 2 * t, 3 * e)

    def test_div(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(1, 2, 3)

        assert s1 / s2 == Shape(x / 1, t / 2, e / 3)

    def test_add_scalar(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        assert s1.add(1) == Shape(x + 1, t + 1, e + 1)

    def test_sub_scalar(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        assert s1.sub(1) == Shape(x - 1, t - 1, e - 1)

    def test_mul_scalar(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        assert s1.mul(2) == Shape(2 * x, 2 * t, 2 * e)

    def test_div_scalar(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        assert s1.truediv(2) == Shape(x / 2, t / 2, e / 2)

    def test_add_unresolved(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(t, e, x)

        assert s1 + s2 == s2 + s1 == Shape(x + t, t + e, e + x)

    def test_sub_unresolved(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = Shape(t, e, x)

        assert s1 - s2 == -s2 - -s1 == Shape(x - t, t - e, e - x)

    def test_get(
        self,
        x: Variable,
        t: Term,
        e: Expression,
        s1: Shape[Variable | Term | Expression],
    ) -> None:
        s2 = s1.get()
        assert s1[0] is x
        assert s1[1] is t
        assert s1[2] is e
        assert s2[0] == 0
        assert s2[1] == 0
        assert s2[2] == 1

    def test_get_mixed_int(self, x) -> None:
        s1 = Shape(x, 2)
        s2 = s1.get()
        assert s1[0] is x
        assert s1[1] == 2
        assert s2[0] == 0
        assert s2[1] == 2

    def test_get_mixed_float(self, x) -> None:
        s1 = Shape(2.0, x)
        s2 = s1.get()
        assert s1[0] == 2.0
        assert s1[1] is x
        assert s2[0] == 2.0
        assert s2[1] == 0


class TestPoint:
    def test_xy(self):
        p = Point(1, 2)
        assert p.x == 1
        assert p.y == 2

    def test_from_polar(self):
        p = Point.from_polar(math.sqrt(25 + 25), math.pi / 4)
        assert math.isclose(p.x, 5)
        assert math.isclose(p.y, 5)

    def test_mag(self):
        p = Point(3, 4)
        assert math.isclose(p.mag, 5)

    def test_radians(self):
        p = Point(5, 5)
        assert math.isclose(p.radians, math.pi / 4)

    def test_unit(self):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue

                p = Point(i, j)
                u = p.unit()
                assert math.isclose(u.mag, 1)

                if i == 0 or j == 0:
                    assert p == u
