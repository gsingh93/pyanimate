from __future__ import annotations

import copy
import math
from typing import Generic, Self, TypeVar, overload

from kiwisolver import Expression, Variable

MaybeInt = int | Variable | Expression
MaybeFloat = float | Variable | Expression
T = TypeVar("T", MaybeInt, MaybeFloat)


class Shape(tuple[T, ...], Generic[T]):
    def __new__(cls, *args: T) -> Self:
        return tuple.__new__(cls, args)

    def add(self, other: T, /) -> Self:
        x = (i + other for i in self)
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __add__(self, other: Self, /) -> Self:
        x = (i + j for i, j in zip(self, other))
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def sub(self, other: T, /) -> Self:
        x = (i - other for i in self)
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __sub__(self, other: Self, /) -> Self:
        x = (i - j for i, j in zip(self, other))
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def mul(self, other: T, /) -> Self:
        x = (i * other for i in self)
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def floormul(self, other: T, /) -> Self:
        x = (int(i * other) for i in self)
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __mul__(self, other: Self, /) -> Self:
        # TODO: Could it lead to bugs if one of the shapes is not resolved? Should we
        # require both to be resolved?
        resolved = self.get()
        other_resolved = other.get()
        x = (i * j for i, j in zip(resolved, other_resolved))
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def floordiv(self, other: T, /) -> Self:
        x = (i // other for i in self)
        return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    # def __floordiv__(self, other: Self, /) -> Self:
    #     x = (i // j for i, j in zip(self, other))
    #     return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    # def truediv(self, other: T, /) -> Self:
    #     x = (i / other for i in self)
    #     return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    # def __truediv__(self, other: Self, /) -> Self:
    #     x = (i / j for i, j in zip(self, other))
    #     return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    # def mod(self, other: T, /) -> Self:
    #     x = (i % other for i in self)
    #     return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    # def __mod__(self, other: Self, /) -> Self:
    #     x = (i % j for i, j in zip(self, other))
    #     return type(self)(*x)  # pyright: ignore[reportGeneralTypeIssues]

    def __radd__(self, other: Self, /) -> Self:
        return self + other

    def __rmul__(self, other: Self, /) -> Self:
        return self * other

    def __str__(self) -> str:
        return f"{type(self).__name__}{tuple(self.get())}"

    @overload
    def get(self: Shape[MaybeInt]) -> Shape[int]:
        ...

    @overload
    def get(self: Shape[MaybeFloat]) -> Shape[float]:
        ...

    def get(self) -> Shape[int] | Shape[float]:
        args = []
        has_float = False
        for i in self:
            if isinstance(i, int):
                assert not has_float
                args.append(i)
            elif isinstance(i, float):
                has_float = True
                args.append(i)
            else:
                args.append(i.value())

        if has_float:
            args = map(float, args)
            return type(self)(*args)
        else:
            args = map(int, args)
            return type(self)(*args)

    def __deepcopy__(
        self,
        memo: dict[int, Self],
    ) -> Self:
        # We need to deepcopy a tuple, not the original object, otherwise the
        # deepcopy implementation will not use the tuple's deepcopy method.
        return type(self)(*copy.deepcopy(tuple(self), memo))  # type: ignore


class Point(Shape[T], Generic[T]):
    @property
    def x(self) -> T:
        return self[0]

    @property
    def y(self) -> T:
        return self[1]

    def __str__(self) -> str:
        return f"P{tuple(self.get())}"

    def mag(self) -> float:
        resolved = self.get()
        return (resolved.x**2 + resolved.y**2) ** 0.5

    def radians(self) -> float:
        resolved = self.get()
        return math.atan2(resolved.y, resolved.x)


class Color(Shape[T], Generic[T]):
    def __new__(  # pylint: disable=arguments-differ
        cls, r: T, g: T, b: T, a: T = 255
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
GREY = Color(128, 128, 128)
GRAY = GREY
WHITE = Color(255, 255, 255)
