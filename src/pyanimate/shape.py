from typing import Generic, Self, TypeVarTuple

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
