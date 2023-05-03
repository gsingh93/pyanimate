from typing import Generic, Self, TypeVar, TypeVarTuple

T = TypeVar("T", int, float)
S = TypeVarTuple("S")


class Shape(tuple, Generic[T, *S]):
    def __new__(cls, arg0: T, *args: *S) -> Self:
        return tuple.__new__(cls, (arg0,) + args)

    def __add__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i + other for i in self)
        else:
            x = (i + j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __sub__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i - other for i in self)
        else:
            x = (i - j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mul__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i * other for i in self)
        else:
            x = (i * j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __floordiv__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i // other for i in self)
        else:
            x = (i // j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __truediv__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i / other for i in self)
        else:
            x = (i / j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mod__(self, other: Self | T, /) -> Self:
        if isinstance(other, (int, float)):
            x = (i % other for i in self)
        else:
            x = (i % j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __radd__(self, other: Self | T, /) -> Self:
        return self + other

    def __rmul__(self, other: Self | T, /) -> Self:
        return self * other


class Point(Shape[T, T], Generic[T]):
    @property
    def x(self) -> T:
        return self[0]

    @property
    def y(self) -> T:
        return self[1]


class Color(Shape[T, T, T], Generic[T]):
    @property
    def r(self) -> T:
        return self[0]

    @property
    def g(self) -> T:
        return self[1]

    @property
    def b(self) -> T:
        return self[2]


BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
WHITE = Color(255, 255, 255)
