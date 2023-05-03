from __future__ import annotations

import copy
from typing import Generic, Self, TypeVar, TypeVarTuple

T = TypeVar("T", int, float)
S = TypeVarTuple("S")


class Shape(tuple[T, ...], Generic[T, *S]):
    def __new__(cls, arg0: T, *args: *S) -> Self:
        return tuple.__new__(cls, (arg0,) + args)

    def add(self, other: T, /) -> Self:
        x = (i + other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __add__(self, other: Self, /) -> Self:
        x = (i + j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def sub(self, other: T, /) -> Self:
        x = (i - other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __sub__(self, other: Self, /) -> Self:
        x = (i - j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def mul(self, other: T, /) -> Self:
        x = (i * other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mul__(self, other: Self, /) -> Self:
        x = (i * j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def floordiv(self, other: T, /) -> Self:
        x = (i // other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __floordiv__(self, other: Self, /) -> Self:
        x = (i // j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def truediv(self, other: T, /) -> Self:
        x = (i / other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __truediv__(self, other: Self, /) -> Self:
        x = (i / j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def mod(self, other: T, /) -> Self:
        x = (i % other for i in self)
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mod__(self, other: Self, /) -> Self:
        x = (i % j for i, j in zip(self, other))
        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __radd__(self, other: Self, /) -> Self:
        return self + other

    def __rmul__(self, other: Self, /) -> Self:
        return self * other

    def __deepcopy__(
        self,
        memo: dict[int, Self],
    ) -> Self:
        # We need to deepcopy a tuple, not the original object, otherwise the
        # deepcopy implementation will not use the tuple's deepcopy method.
        return Shape(*copy.deepcopy(tuple(self)))  # type: ignore


class Point(Shape[T, T], Generic[T]):
    @property
    def x(self) -> T:
        return self[0]

    @property
    def y(self) -> T:
        return self[1]


class Color(Shape[T, T, T], Generic[T]):
    def __new__(  # pylint: disable=arguments-differ
        cls, r: T, g: T, b: T, a: T = 0
    ) -> Self:
        return tuple.__new__(cls, (r, g, b, a))

    @staticmethod
    def from_alpha(alpha: T) -> Color[T]:
        zero = type(alpha)(0)
        return Color(zero, zero, zero, alpha)

    @property
    def r(self) -> T:
        return self[0]

    @property
    def g(self) -> T:
        return self[1]

    @property
    def b(self) -> T:
        return self[2]

    @property
    def a(self) -> T:
        return self[3]


BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
WHITE = Color(255, 255, 255)
