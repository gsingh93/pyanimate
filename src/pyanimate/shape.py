from typing import Generic, Self, TypeAlias, TypeVarTuple

S = TypeVarTuple("S")


class Shape(tuple, Generic[*S]):
    def __new__(cls, *args: *S) -> Self:
        return tuple.__new__(Shape, args)

    def __add__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i + other for i in self)
        else:
            x = (i + j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __sub__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i - other for i in self)
        else:
            x = (i - j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mul__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i * other for i in self)
        else:
            x = (i * j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __floordiv__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i // other for i in self)
        else:
            x = (i // j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __truediv__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i / other for i in self)
        else:
            x = (i / j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mod__(self, other: Self | int, /) -> Self:
        if isinstance(other, int):
            x = (i % other for i in self)
        else:
            x = (i % j for i, j in zip(self, other))

        return Shape(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __radd__(self, other: Self | int, /) -> Self:
        return self + other

    def __rmul__(self, other: Self | int, /) -> Self:
        return self * other


Point: TypeAlias = Shape[int, int]
Color: TypeAlias = Shape[int, int, int]
